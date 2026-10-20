"""Riconoscimento ottico dei caratteri (OCR) per immagini e PDF scansionati, tramite Tesseract."""

from __future__ import annotations

import re
from functools import lru_cache

from .external import find_program
from .i18n import _
from .model import Block, Line


@lru_cache(maxsize=1)
def _tesseract():
    path = find_program("tesseract")
    if not path:
        return None
    try:
        import pytesseract
    except ImportError:
        return None
    pytesseract.pytesseract.tesseract_cmd = path
    return pytesseract


def available() -> bool:
    return _tesseract() is not None


@lru_cache(maxsize=8)
def language_string(preferred: str) -> str:
    """Usa le lingue richieste che risultano installate (es. "ita+eng")."""
    tess = _tesseract()
    try:
        installed = set(tess.get_languages(config=""))
    except Exception:
        return preferred
    chosen = [lang for lang in preferred.split("+") if lang in installed]
    if chosen:
        return "+".join(chosen)
    return "eng" if "eng" in installed else (sorted(installed - {"osd"}) or ["eng"])[0]


_OCR_BULLET_RE = re.compile(r"^(?:e|o|°|•|·|\*|»|«|=|¢|©|®)\s+(?=[A-ZÀ-Ý0-9])")
# Richiami di nota in apice che l'OCR legge come apostrofi o asterischi: "parola' e" -> "parola e".
_OCR_MARKER_RE = re.compile(r"(?<=\d)[’'*?¹²³]+(?=\s+[a-zà-ù])")


def _fix_ocr_line(text: str, first: bool) -> str:
    if first:
        text = _OCR_BULLET_RE.sub("• ", text)
    return _OCR_MARKER_RE.sub("", text)


def image_blocks(image, languages: str) -> tuple[list[Block], float]:
    """Restituisce i blocchi di testo riconosciuti e l'altezza dell'immagine.

    Tesseract divide la pagina in blocchi e paragrafi: li conserviamo, con la loro
    posizione, per poter riconoscere intestazioni, numeri di pagina e note.
    """
    tess = _tesseract()
    if tess is None:
        raise RuntimeError(_("Tesseract non è installato"))
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    # Tesseract lavora meglio a circa 300 dpi: le immagini piccole vengono ingrandite.
    longest = max(image.size)
    if longest < 3000:
        from PIL import Image

        factor = min(3.0, 3300 / longest)
        image = image.resize((int(image.width * factor), int(image.height * factor)), Image.LANCZOS)
    data = tess.image_to_data(image, lang=language_string(languages), config="--psm 3",
                              output_type=tess.Output.DICT)
    paragraphs: dict[tuple, dict[int, list[int]]] = {}
    for i, word in enumerate(data["text"]):
        if not word.strip():
            continue
        try:
            if float(data["conf"][i]) < 0:
                continue
        except (TypeError, ValueError):
            pass
        key = (data["block_num"][i], data["par_num"][i])
        paragraphs.setdefault(key, {}).setdefault(data["line_num"][i], []).append(i)

    blocks = []
    for key in sorted(paragraphs):
        lines = []
        for line_no in sorted(paragraphs[key]):
            idx = paragraphs[key][line_no]
            words = [data["text"][i] for i in idx]
            x0 = min(data["left"][i] for i in idx)
            y0 = min(data["top"][i] for i in idx)
            x1 = max(data["left"][i] + data["width"][i] for i in idx)
            y1 = max(data["top"][i] + data["height"][i] for i in idx)
            heights = sorted(data["height"][i] for i in idx)
            text = _fix_ocr_line(" ".join(words), first=not lines)
            lines.append(Line(text, x0, y0, x1, y1, float(heights[len(heights) // 2])))
        if lines and lines[0].text.startswith("• "):
            # Elenco puntato: le altre voci allineate alla prima hanno lo stesso simbolo mal letto.
            for line in lines[1:]:
                if abs(line.x0 - lines[0].x0) <= max(4, lines[0].size * 0.3):
                    line.text = _OCR_BULLET_RE.sub("• ", line.text)
        if lines:
            blocks.append(Block(lines, raw_start=lines[0].text[:12]))
    return blocks, float(image.height)
