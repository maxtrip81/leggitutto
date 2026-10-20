"""Pulizia del testo: toglie tutto ciò che disturba la lettura con sintesi vocale o braille.

Numeri di pagina, intestazioni e piè di pagina ripetuti, note, richiami di nota,
sillabazioni a fine riga, righe spezzate, puntini degli indici, caratteri invisibili.
"""

from __future__ import annotations

import re
import textwrap
import unicodedata
from collections import Counter

from .model import Extracted, Para
from .settings import Options

# ---------------------------------------------------------------------------
# Caratteri

_LIGATURES = {
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi",
    "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st", "Ĳ": "IJ", "ĳ": "ij",
}
# Elenchi puntati scritti con font simbolici (area privata Unicode).
_PUA_BULLETS = {"": "•", "": "•", "": "•", "": "•", "": "•", "": "•", "": "-"}
_INVISIBLE = dict.fromkeys(map(ord, "­​‌‍⁠﻿‎‏‪‫‬‭‮⁡⁢⁣"), None)
_SPACES_RE = re.compile("[   -   　\t]")
_CONTROL_RE = re.compile("[\x00-\x08\x0b\x0e-\x1f\x7f-\x9f]")
_PUA_RE = re.compile("[-]")
_SUPERSCRIPTS = "⁰¹²³⁴⁵⁶⁷⁸⁹"


def normalize_chars(text: str) -> str:
    for src, dst in _LIGATURES.items():
        text = text.replace(src, dst)
    for src, dst in _PUA_BULLETS.items():
        text = text.replace(src, dst)
    text = text.translate(_INVISIBLE)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\f", "\n\n").replace("\v", "\n").replace(" ", "\n").replace(" ", "\n\n")
    text = _SPACES_RE.sub(" ", text)
    text = _CONTROL_RE.sub("", text)
    text = _PUA_RE.sub("", text)
    return unicodedata.normalize("NFC", text)


# ---------------------------------------------------------------------------
# Richiami di nota nel testo: "parola¹", "parola[12]", "parola.3" non si tocca.

_UNITS = ("m", "cm", "mm", "km", "dm", "ft", "in", "mq")
_SUP_RE = re.compile(rf"([^\W{_SUPERSCRIPTS}]+|[.,;:!?)\]»”\"'’])([{_SUPERSCRIPTS}]+)")
_BRACKET_REF_RE = re.compile(r"(?<=[\w.,;:!?)»”\"'’])\s?\[(?:\d{1,3}(?:\s?[,\-–]\s?\d{1,3})*|[a-z]|nota\s\d{1,3}|note\s\d{1,3})\]", re.I)
_CARET_REF_RE = re.compile(r"\^\d{1,3}\b|\[\^\w+\]")


def remove_note_markers(text: str) -> str:
    def sup(match):
        word = match.group(1)
        return match.group(0) if word.lower() in _UNITS else word

    text = _SUP_RE.sub(sup, text)
    text = _BRACKET_REF_RE.sub("", text)
    return _CARET_REF_RE.sub("", text)


# ---------------------------------------------------------------------------
# Numeri di pagina

_ROMAN_RE = re.compile(r"^[-–—\s]*(?=[mdclxvi])m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})[-–—\s]*$")
_PAGE_RES = [
    re.compile(r"^[-–—~|•·\[(<\s]*\d{1,4}[-–—~|•·\])>\s]*$"),
    re.compile(
        r"^(?:pag(?:ina|\.)?|pagg?\.|pg\.?|p\.|page|seite|s\.|página|folio|f\.)\s*\d{1,4}"
        r"(?:\s*(?:di|of|/|von|de|su|sur)\s*\d{1,4})?\s*$",
        re.I,
    ),
    re.compile(r"^\d{1,4}\s*(?:/|di|of|su|von|de)\s*\d{1,4}$", re.I),
]


def is_page_number(text: str, allow_roman: bool = True) -> bool:
    t = text.strip()
    if not t or len(t) > 25:
        return False
    if any(rx.match(t) for rx in _PAGE_RES):
        return True
    return allow_roman and bool(_ROMAN_RE.match(t))


# ---------------------------------------------------------------------------
# Elementi decorativi

_DECORATION_RE = re.compile(r"^[\s\-–—_=~*•·.:#+<>|/\\°^]{3,}$")
_TOC_LEADER_RE = re.compile(r"^(.{2,}?)\s*(?:[.·…_]\s*){4,}\s*(?:\d{1,4}|[ivxlcdm]{1,7})\s*$", re.I)
_PAGE_MARKER_RE = re.compile(r"^\s*[-–—=\[(]*\s*(?:pagina|page|pag\.)\s*\d{1,4}\s*[-–—=\])]*\s*$", re.I)


def is_decoration(text: str) -> bool:
    return bool(_DECORATION_RE.match(text))


def strip_toc_leaders(text: str) -> str:
    return _TOC_LEADER_RE.sub(r"\1", text)


# ---------------------------------------------------------------------------
# Righe spezzate e sillabazione

_BULLET_RE = re.compile(r"^\s*(?:[•●○◦▪▫■□►▶➢➤✓✔◆◇–—*-]\s+|\(?\d{1,3}[.)]\s+|\(?[a-zA-Z][.)]\s+)")
_TERMINAL_RE = re.compile(r"[.!?:;…»”\"’)\]]$")


def join_lines(lines: list[str]) -> str:
    """Unisce le righe di un paragrafo, ricomponendo le parole sillabate."""
    out = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not out:
            out = line
        elif re.search(r"[^\W\d_]-$", out) and line[:1].islower():
            out = out[:-1] + line  # "proble-" + "ma" -> "problema"
        elif out.endswith(("-", "/")) and not out.endswith((" -", " /")):
            out += line  # "Emilia-" + "Romagna"
        else:
            out += " " + line
    return out


def starts_list_item(text: str) -> bool:
    return bool(_BULLET_RE.match(text))


def reflow_plain_text(text: str) -> list[Para]:
    """Ricompone i paragrafi di un testo semplice con a capo forzati (es. 70 colonne)."""
    lines = text.split("\n")
    lengths = sorted(len(l.strip()) for l in lines if l.strip())
    if not lengths:
        return []
    width = lengths[int(len(lengths) * 0.9)] if len(lengths) >= 10 else max(lengths)
    hard_wrapped = 40 <= width <= 110 and len(lengths) >= 5
    paras: list[Para] = []
    current: list[str] = []

    def flush():
        if current:
            paras.append(Para(join_lines(current)))
            current.clear()

    for raw in lines:
        line = raw.strip()
        if not line:
            flush()
            continue
        if current and starts_list_item(line):
            flush()
        current.append(line)
        # Una riga corta chiude il paragrafo: è l'ultima riga, un titolo o un verso.
        if not hard_wrapped or len(line) < width * 0.65:
            flush()
    flush()
    return paras


# ---------------------------------------------------------------------------
# Documenti impaginati: intestazioni e piè di pagina ripetuti

def _hf_key(text: str) -> str:
    key = re.sub(r"\d+", "#", text.lower())
    key = re.sub(r"\b[ivxlcdm]+\b", "#", key)
    return re.sub(r"\s+", " ", key).strip(" .-–—|•·")


def _edge_indexes(page: list[Para]) -> list[int]:
    n = len(page)
    return sorted({i for i in (0, 1, n - 2, n - 1) if 0 <= i < n})


def remove_running_heads(pages: list[list[Para]]) -> list[list[Para]]:
    """Toglie le righe che si ripetono in cima o in fondo a molte pagine.

    Per le righe che la posizione sulla pagina indica come intestazione o piè di pagina,
    i numeri vengono ignorati nel confronto ("Capitolo 3 - 45" = "Capitolo 3 - 46");
    per le altre si richiede il testo identico, così i titoli "Capitolo 1", "Capitolo 2"
    in cima alle pagine non vengono scambiati per intestazioni.
    """
    if len(pages) < 3:
        return pages
    loose: Counter[str] = Counter()
    exact: Counter[str] = Counter()
    for page in pages:
        edge = [page[i] for i in _edge_indexes(page) if len(page[i].text) <= 160]
        loose.update({_hf_key(p.text) for p in edge if p.zone != "body"} - {""})
        exact.update({p.text.strip().lower() for p in edge} - {""})
    edge_threshold = max(3, int(len(pages) * 0.2))
    result = []
    for page in pages:
        edges = set(_edge_indexes(page))
        kept = []
        for i, para in enumerate(page):
            if i in edges and len(para.text) <= 160:
                if para.zone != "body" and loose[_hf_key(para.text)] >= 3:
                    continue
                if exact[para.text.strip().lower()] >= edge_threshold:
                    continue
            kept.append(para)
        result.append(kept)
    return result


def merge_pages(pages: list[list[Para]]) -> list[Para]:
    """Concatena le pagine riunendo i paragrafi spezzati dal cambio pagina."""
    out: list[Para] = []
    for page in pages:
        for i, para in enumerate(page):
            if i == 0 and out and out[-1].kind == "text" and para.kind in ("text", "list"):
                prev = out[-1].text
                first = para.text[:1]
                hyphen = re.search(r"[^\W\d_]-$", prev) is not None
                if (not _TERMINAL_RE.search(prev) and first.islower()) or (hyphen and first.islower()):
                    out[-1] = Para(join_lines([prev, para.text]), kind="text")
                    continue
            out.append(para)
    return out


# ---------------------------------------------------------------------------
# Rifinitura finale

def _tidy_paragraph(text: str, opts: Options) -> str:
    text = normalize_chars(text)
    if opts.remove_note_markers:
        text = remove_note_markers(text)
    if opts.remove_decorations:
        text = strip_toc_leaders(text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r" +([,.;:!?)\]»”])", r"\1", text)
    text = re.sub(r"([(\[«“]) +", r"\1", text)
    return text.strip()


def _wrap(text: str, width: int) -> str:
    if width <= 0:
        return text
    out = []
    for line in text.split("\n"):
        out.append(textwrap.fill(line, width, break_long_words=False, break_on_hyphens=False) if line else "")
    return "\n".join(out)


def finalize(extracted: Extracted, opts: Options) -> str:
    if extracted.final is not None:
        text = normalize_chars(extracted.final)
        text = re.sub(r"[ ]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return _wrap(text, opts.wrap_width) + "\n"

    if extracted.pages is not None:
        pages = [[p for p in page if p.text.strip()] for page in extracted.pages]
        if opts.remove_page_numbers:
            pages = [[p for p in page if not is_page_number(p.text, allow_roman=p.zone != "body")] for page in pages]
        if opts.remove_headers_footers:
            pages = remove_running_heads(pages)
            pages = [[p for p in page if not (p.zone != "body" and opts.remove_page_numbers and is_page_number(p.text))] for page in pages]
        paras = merge_pages(pages)
    else:
        paras = list(extracted.paras or [])

    blocks: list[str] = []
    for para in paras:
        raw = para.text
        if para.kind == "pre":
            text = normalize_chars(raw).strip("\n")
            if text.strip():
                blocks.append(text)
            continue
        text = "\n".join(_tidy_paragraph(line, opts) for line in raw.split("\n"))
        text = re.sub(r"\n{2,}", "\n", text).strip()
        if not text:
            continue
        if opts.remove_page_numbers and is_page_number(text, allow_roman=False):
            continue
        if opts.remove_page_numbers and _PAGE_MARKER_RE.match(text):
            continue
        if opts.remove_decorations and is_decoration(text):
            continue
        blocks.append(text)

    # Toglie i paragrafi duplicati consecutivi (frequenti negli OCR e nelle intestazioni).
    deduped: list[str] = []
    for block in blocks:
        if not deduped or block != deduped[-1]:
            deduped.append(block)
    text = "\n\n".join(deduped)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return _wrap(text, opts.wrap_width) + "\n" if text else ""
