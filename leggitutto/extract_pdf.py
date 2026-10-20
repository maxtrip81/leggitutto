"""Estrazione da PDF (anche protetti da password), XPS, CBZ e immagini scansionate.

Il testo viene letto con la sua posizione e dimensione sulla pagina: così si possono
riconoscere e scartare numeri di pagina, intestazioni, piè di pagina e note.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from . import ocr
from .cleaner import join_lines, starts_list_item
from .i18n import _
from .model import Block, ConversionError, Context, Extracted, Line, Para, ProtectedError
from .settings import Options

_FOOTNOTE_START_RE = re.compile(r"^\s*(?:\d{1,3}|[*†‡§¶]+|[¹²³⁴⁵⁶⁷⁸⁹⁰]+|\(\d{1,3}\)|\[\d{1,3}\]|[a-z]\))(?:[\s.)\]:]|[A-Za-zÀ-ÿ«\"“])")
_TERMINAL_RE = re.compile(r"[.!?:;…»”\"’)]$")
_MARKER_RE = re.compile(r"^[\d*†‡§¶,\-–\s]{1,6}$")


def _pymupdf():
    try:
        import pymupdf
    except ImportError:  # versioni vecchie
        import fitz as pymupdf
    return pymupdf


# ---------------------------------------------------------------------------
# Dai blocchi posizionati ai paragrafi (condiviso fra PDF e OCR)

def _zone(block: Block, page_h: float) -> str:
    if len(block.lines) <= 2 and block.y1 <= page_h * 0.10:
        return "top"
    if len(block.lines) <= 3 and block.y0 >= page_h * 0.90:
        return "bottom"
    return "body"


class Metrics:
    """Soglie di confronto fra dimensioni del testo. Nell'OCR le misure sono meno precise."""

    def __init__(self, heading=1.15, size_jump=0.15, small=0.9):
        self.heading, self.size_jump, self.small = heading, size_jump, small


PDF_METRICS = Metrics()
OCR_METRICS = Metrics(heading=1.5, size_jump=0.45, small=0.9)


def _is_heading(lines: list[Line], body: float, m: Metrics = PDF_METRICS) -> bool:
    text = " ".join(l.text for l in lines)
    if len(text) > 200:
        return False
    size = sum(l.size for l in lines) / len(lines)
    return size >= body * m.heading or (all(l.bold for l in lines) and len(lines) <= 2 and len(text) < 120 and not text.endswith("."))


def blocks_to_paras(blocks: list[Block], page_h: float, body: float, opts: Options, m: Metrics = PDF_METRICS) -> list[Para]:
    paras: list[Para] = []
    body_lines: list[tuple[Line, int]] = []
    in_notes = False
    edge_paras: list[Para] = []

    for index, block in enumerate(blocks):
        if block.table is not None:
            body_lines.append((None, block.table))
            continue
        if not block.lines:
            continue
        zone = _zone(block, page_h)
        if opts.remove_footnotes and zone != "top":
            small = block.size <= body * m.small
            if small and block.y0 > page_h * 0.45 and (in_notes or _FOOTNOTE_START_RE.match(block.raw_start or block.text)):
                in_notes = True
                continue
        if zone != "body":
            edge_paras.append(Para(join_lines([l.text for l in block.lines]), zone=zone))
            continue
        body_lines.extend((line, index) for line in block.lines)

    # Bordo destro della colonna di ogni riga: serve a capire se una riga è "piena".
    def right_edge(line: Line) -> float:
        tol = 3 * max(line.size, 1)
        return max((l.x1 for l, _idx in body_lines if l is not None and abs(l.x0 - line.x0) <= tol), default=line.x1)

    current: list[Line] = []

    def flush():
        if current:
            kind = "heading" if _is_heading(current, body, m) else ("list" if starts_list_item(current[0].text) else "text")
            paras.append(Para(join_lines([l.text for l in current]), kind=kind))
            current.clear()

    prev_block = None
    for line, block_index in body_lines:
        if line is None:  # tabella
            flush()
            paras.extend(block_index)
            prev_block = None
            continue
        if current:
            prev = current[-1]
            s = max(prev.size, 1.0)
            gap = line.y0 - prev.y1
            same_column = gap > -0.5 * s
            prev_short = prev.x1 < right_edge(prev) - max(2 * s, 0.1 * (right_edge(prev) - prev.x0))
            new = (
                starts_list_item(line.text)
                or abs(line.size - prev.size) > m.size_jump * s
                or line.bold != prev.bold and (len(line.text) < 80 or len(prev.text) < 80) and _is_heading(current, body, m)
                or gap > 0.65 * s
                or (same_column and line.x0 > prev.x0 + 0.9 * s)
                or (prev_short and _TERMINAL_RE.search(prev.text) is not None)
                or (block_index != prev_block and _TERMINAL_RE.search(prev.text) is not None and gap > 0.2 * s)
                or (prev_short and len(current) == 1 and _is_heading(current, body, m))
            )
            if new:
                flush()
        current.append(line)
        prev_block = block_index
    flush()

    tops = [p for p in edge_paras if p.zone == "top"]
    bottoms = [p for p in edge_paras if p.zone == "bottom"]
    return tops + paras + bottoms


def _body_size(sizes: Counter) -> float:
    if not sizes:
        return 10.0
    return float(sizes.most_common(1)[0][0])


# ---------------------------------------------------------------------------
# PDF

def _open_document(path: Path, ctx: Context, filetype: str | None = None):
    pymupdf = _pymupdf()
    try:
        doc = pymupdf.open(str(path), filetype=filetype) if filetype else pymupdf.open(str(path))
    except Exception as exc:
        raise ConversionError(_("il file non si apre (forse è danneggiato): {exc}").format(exc=exc)) from exc
    if doc.needs_pass:
        for attempt in range(3):
            password = ctx.ask_password(path.name, attempt)
            if password is None:
                raise ProtectedError(_("il documento è protetto da password e non è stata inserita la password."))
            if doc.authenticate(password):
                break
        else:
            raise ProtectedError(_("la password inserita non è corretta."))
    return doc


def _page_blocks(page, opts: Options, sizes: Counter | None = None) -> list[Block]:
    pymupdf = _pymupdf()
    flags = pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_MEDIABOX_CLIP
    data = page.get_text("dict", flags=flags)
    blocks = []
    for raw_block in data.get("blocks", []):
        if raw_block.get("type", 0) != 0:
            continue
        lines = []
        raw_start = ""
        for raw_line in raw_block.get("lines", []):
            dx, dy = raw_line.get("dir", (1, 0))
            if abs(dy) > 0.3 and opts.remove_decorations:
                continue  # testo verticale nei margini (codici, filigrane)
            spans = [s for s in raw_line.get("spans", []) if s.get("text")]
            if not spans:
                continue
            if not raw_start:
                raw_start = "".join(s["text"] for s in spans)[:12]
            max_size = max(s["size"] for s in spans)
            baseline = max(spans, key=lambda s: s["size"])["origin"][1]
            parts, chars, weighted, bold = [], 0, 0.0, True
            last_x1 = None
            for span in sorted(spans, key=lambda s: s["bbox"][0]):
                text = span["text"]
                is_marker = (
                    opts.remove_note_markers
                    and _MARKER_RE.match(text.strip() or "x")
                    and (span["flags"] & 1 or (span["size"] < max_size * 0.8 and span["origin"][1] < baseline - 0.15 * max_size))
                )
                if is_marker:
                    continue
                if last_x1 is not None and span["bbox"][0] - last_x1 > 0.25 * span["size"]:
                    if parts and not parts[-1].endswith(" ") and not text.startswith(" "):
                        parts.append(" ")
                parts.append(text)
                last_x1 = span["bbox"][2]
                n = len(text.strip())
                chars += n
                weighted += span["size"] * n
                if n and not (span["flags"] & 16 or "bold" in span.get("font", "").lower()):
                    bold = False
            text = re.sub(r"\s+", " ", "".join(parts)).strip()
            if not text:
                continue
            size = weighted / chars if chars else max_size
            if sizes is not None:
                sizes[round(size * 2) / 2] += len(text)
            x0, y0, x1, y1 = raw_line["bbox"]
            lines.append(Line(text, x0, y0, x1, y1, size, bold))
        if lines:
            blocks.append(Block(lines, raw_start=raw_start))
    return _insert_tables(page, blocks)


def _insert_tables(page, blocks: list[Block]) -> list[Block]:
    """Le tabelle con bordi vengono lette riga per riga, nel formato "Intestazione: valore"."""
    from .extract_office import table_to_paras

    try:
        tables = [t for t in page.find_tables().tables if t.row_count >= 2 and t.col_count >= 2]
    except Exception:
        return blocks
    if not tables:
        return blocks
    result = []
    placed = set()
    for block in blocks:
        cx, cy = (block.x0 + block.x1) / 2, (block.y0 + block.y1) / 2
        inside = next((i for i, t in enumerate(tables) if t.bbox[0] <= cx <= t.bbox[2] and t.bbox[1] <= cy <= t.bbox[3]), None)
        if inside is None:
            result.append(block)
        elif inside not in placed:
            placed.add(inside)
            rows = [[c or "" for c in row] for row in tables[inside].extract()]
            result.append(Block([], table=table_to_paras(rows)))
    return result


def _looks_garbled(text: str) -> bool:
    if not text:
        return False
    bad = sum(1 for ch in text if ch == "�" or "" <= ch <= "" or (ord(ch) < 32 and ch not in "\n\t"))
    return bad / len(text) > 0.25


def _ocr_page(page, opts: Options) -> list[Para]:
    from PIL import Image

    pix = page.get_pixmap(dpi=300, alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return ocr_image_paras(image, opts)


def ocr_image_paras(image, opts: Options) -> list[Para]:
    blocks, height = ocr.image_blocks(image, opts.ocr_languages)
    sizes = Counter()
    for b in blocks:
        for l in b.lines:
            sizes[round(l.size)] += len(l.text)
    return blocks_to_paras(blocks, height, _body_size(sizes), opts, OCR_METRICS)


def extract_pdf(path: Path, opts: Options, ctx: Context, filetype: str | None = None) -> Extracted:
    doc = _open_document(path, ctx, filetype)
    result = Extracted(pages=[])
    total = len(doc)
    if total == 0:
        raise ConversionError(_("il documento non contiene pagine."))

    # Primo passaggio: dimensione del carattere del corpo del testo.
    ctx.progress(0.0, _("Analisi dell'impaginazione"))
    sizes: Counter = Counter()
    cached: dict[int, list[Block]] = {}
    for i in range(min(total, 80)):
        ctx.check_cancel()
        cached[i] = _page_blocks(doc[i], opts, sizes)
    body = _body_size(sizes)

    ocr_warned = False
    for i in range(total):
        ctx.progress(i / total, _("Pagina {n} di {total}").format(n=i + 1, total=total))
        page = doc[i]
        blocks = cached.pop(i, None)
        if blocks is None:
            blocks = _page_blocks(page, opts)
        text = " ".join(b.text for b in blocks if b.lines)
        needs_ocr = (len(text.strip()) < 25 and page.get_images()) or _looks_garbled(text)
        if needs_ocr and opts.ocr:
            if ocr.available():
                try:
                    result.pages.append(_ocr_page(page, opts))
                    continue
                except Exception as exc:  # l'OCR di una pagina non deve fermare tutto
                    ctx.warn(_("OCR non riuscito a pagina {n}: {exc}").format(n=i + 1, exc=exc))
            elif not ocr_warned:
                ctx.warn(_("il documento contiene immagini o pagine scansionate: per leggerle installa Tesseract OCR (vedi la Guida, tasto F1)."))
                ocr_warned = True
        result.pages.append(blocks_to_paras(blocks, page.rect.height, body, opts))
    doc.close()
    if not any(result.pages) and not ocr_warned:
        ctx.warn(_("nel documento non è stato trovato testo leggibile."))
    return result


def extract_image(path: Path, opts: Options, ctx: Context) -> Extracted:
    from PIL import Image, ImageSequence

    if not ocr.available():
        raise ConversionError(_("il file è un'immagine: per leggerne il testo installa Tesseract OCR (vedi la Guida, tasto F1)."))
    try:
        img = Image.open(path)
    except Exception as exc:
        raise ConversionError(_("immagine non leggibile: {exc}").format(exc=exc)) from exc
    frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
    pages = []
    for i, frame in enumerate(frames):
        ctx.progress(i / len(frames), _("Riconoscimento del testo, immagine {n} di {total}").format(n=i + 1, total=len(frames)))
        pages.append(ocr_image_paras(frame, opts))
    return Extracted(pages=pages)
