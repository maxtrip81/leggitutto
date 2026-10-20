"""Riconosce il formato di un file e lo trasforma in un file .txt pulito."""

from __future__ import annotations

import os
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from typing import Callable

from . import extract_office as office
from . import extract_pdf as pdf
from . import extract_web as web
from .cleaner import finalize
from .model import ConversionError, Context, Extracted, Para
from .settings import Options

AUDIO_VIDEO = {
    ".mp3", ".wav", ".m4a", ".m4b", ".aac", ".flac", ".ogg", ".oga", ".opus", ".wma", ".aif", ".aiff",
    ".amr", ".mka", ".ac3", ".caf", ".mp2", ".au", ".3ga", ".weba", ".spx",
    ".mp4", ".m4v", ".mov", ".avi", ".mkv", ".webm", ".wmv", ".flv", ".mpg", ".mpeg", ".3gp", ".3g2",
    ".ts", ".mts", ".m2ts", ".ogv", ".vob", ".asf", ".rm", ".rmvb", ".divx", ".f4v",
}
IMAGES = {".png", ".jpg", ".jpeg", ".jpe", ".tif", ".tiff", ".bmp", ".gif", ".webp", ".jp2", ".pnm", ".pbm", ".pgm", ".ppm", ".pcx"}


def _media(path, opts, ctx):
    from .media import transcribe

    return transcribe(path, opts, ctx)


def _pdf_type(filetype):
    return lambda path, opts, ctx: pdf.extract_pdf(path, opts, ctx, filetype=filetype)


Extractor = Callable[[Path, Options, Context], Extracted]

BY_EXTENSION: dict[str, Extractor] = {
    ".pdf": pdf.extract_pdf, ".xps": _pdf_type("xps"), ".oxps": _pdf_type("xps"), ".cbz": _pdf_type("cbz"),
    ".docx": office.extract_docx, ".docm": office.extract_docx, ".dotx": office.extract_docx, ".dotm": office.extract_docx,
    ".doc": office.extract_legacy_office, ".dot": office.extract_legacy_office, ".wps": office.extract_legacy_office,
    ".wpd": office.extract_legacy_office, ".lwp": office.extract_legacy_office, ".sxw": office.extract_legacy_office,
    ".ppt": office.extract_legacy_office, ".pps": office.extract_legacy_office, ".pot": office.extract_legacy_office,
    ".fodt": office.extract_legacy_office, ".fodp": office.extract_legacy_office, ".fods": office.extract_legacy_office,
    ".hwp": office.extract_legacy_office, ".abw": office.extract_legacy_office, ".pub": office.extract_legacy_office,
    ".odt": office.extract_odf, ".ott": office.extract_odf, ".ods": office.extract_odf, ".ots": office.extract_odf,
    ".odp": office.extract_odf, ".otp": office.extract_odf,
    ".rtf": office.extract_rtf,
    ".pptx": office.extract_pptx, ".pptm": office.extract_pptx, ".ppsx": office.extract_pptx, ".potx": office.extract_pptx,
    ".xlsx": office.extract_xlsx, ".xlsm": office.extract_xlsx, ".xltx": office.extract_xlsx, ".xltm": office.extract_xlsx,
    ".xls": office.extract_xls, ".csv": office.extract_csv, ".tsv": office.extract_csv,
    ".epub": web.extract_epub, ".fb2": web.extract_fb2, ".fbz": web.extract_fb2,
    ".mobi": web.extract_ebook_other, ".azw": web.extract_ebook_other, ".azw3": web.extract_ebook_other,
    ".prc": web.extract_ebook_other, ".pdb": web.extract_ebook_other, ".lit": web.extract_ebook_other,
    ".lrf": web.extract_ebook_other, ".djvu": web.extract_ebook_other, ".djv": web.extract_ebook_other,
    ".chm": web.extract_ebook_other, ".snb": web.extract_ebook_other, ".tcr": web.extract_ebook_other,
    ".rb": web.extract_ebook_other, ".kfx": web.extract_ebook_other, ".azw4": web.extract_ebook_other,
    ".html": web.extract_html, ".htm": web.extract_html, ".xhtml": web.extract_html, ".shtml": web.extract_html,
    ".mht": web.extract_mht, ".mhtml": web.extract_mht,
    ".md": web.extract_markdown, ".markdown": web.extract_markdown,
    ".srt": web.extract_subtitles, ".vtt": web.extract_subtitles, ".ass": web.extract_subtitles, ".ssa": web.extract_subtitles,
    ".txt": web.extract_plain_text, ".text": web.extract_plain_text, ".log": web.extract_plain_text, ".nfo": web.extract_plain_text,
    ".xml": web.extract_xml, ".json": web.extract_json,
}
for _ext in AUDIO_VIDEO:
    BY_EXTENSION[_ext] = _media
for _ext in IMAGES:
    BY_EXTENSION[_ext] = pdf.extract_image


def _sniff(path: Path) -> Extractor | None:
    """Riconosce il formato dal contenuto, per file senza estensione o con estensione sconosciuta."""
    with open(path, "rb") as fh:
        head = fh.read(4096)
    if head.startswith(b"%PDF") or b"%PDF-" in head[:1024]:
        return pdf.extract_pdf
    if head.startswith(b"PK"):
        try:
            with zipfile.ZipFile(path) as zf:
                names = set(zf.namelist())
                mimetype = zf.read("mimetype").decode("ascii", "ignore") if "mimetype" in names else ""
        except zipfile.BadZipFile:
            return None
        if "word/document.xml" in names:
            return office.extract_docx
        if "ppt/presentation.xml" in names:
            return office.extract_pptx
        if "xl/workbook.xml" in names:
            return office.extract_xlsx
        if "epub" in mimetype:
            return web.extract_epub
        if "opendocument" in mimetype:
            return office.extract_odf
        return extract_archive
    if head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        if b"E\x00n\x00c\x00r\x00y\x00p\x00t\x00i\x00o\x00n\x00I\x00n\x00f\x00o" in open(path, "rb").read(1 << 20):
            return _encrypted_ooxml
        return office.extract_legacy_office
    if head.lstrip().startswith(b"{\\rtf"):
        return office.extract_rtf
    if head[60:68] in (b"BOOKMOBI", b"TEXtREAd") or head.startswith(b"AT&TFORM") or head.startswith(b"ITSF"):
        return web.extract_ebook_other
    lower = head.lower()
    if b"<html" in lower or b"<!doctype html" in lower:
        return web.extract_html
    if b"fictionbook" in lower:
        return web.extract_fb2
    if lower.lstrip().startswith(b"<?xml"):
        return web.extract_xml
    if b"-->" in head and b"\n1\n" in head.replace(b"\r", b"") or head.startswith(b"WEBVTT"):
        return web.extract_subtitles
    try:
        from PIL import Image

        with Image.open(path) as img:
            img.verify()
        return pdf.extract_image
    except Exception:
        pass
    try:
        import av

        with av.open(str(path)) as container:
            if container.streams.audio:
                return _media
    except Exception:
        pass
    sample = head[:2048]
    if sample and sum(1 for b in sample if b < 9 or 13 < b < 32) / len(sample) < 0.02:
        return web.extract_plain_text
    return None


def _encrypted_ooxml(path: Path, opts: Options, ctx: Context) -> Extracted:
    data = office.decrypt_office(path, ctx)
    if data is None:
        raise ConversionError("documento Office non riconosciuto.")
    with zipfile.ZipFile(data) as zf:
        names = set(zf.namelist())
    data.seek(0)
    if "ppt/presentation.xml" in names:
        return office.extract_pptx(path, opts, ctx, data=data)
    if "xl/workbook.xml" in names:
        return office.extract_xlsx(path, opts, ctx, data=data)
    return office.extract_docx(path, opts, ctx, data=data)


def extract_archive(path: Path, opts: Options, ctx: Context) -> Extracted:
    """Archivio .zip: converte uno dopo l'altro tutti i file che contiene."""
    paras: list[Para] = []
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(path) as zf:
        members = [m for m in zf.infolist() if not m.is_dir() and not m.filename.startswith(("__MACOSX/", ".")) and "/." not in m.filename]
        for n, member in enumerate(sorted(members, key=lambda m: m.filename.lower())):
            name = Path(member.filename).name
            if not name or name.startswith("."):
                continue
            target = Path(tmp) / f"{n:04d}_{name}"
            try:
                with zf.open(member) as src:
                    target.write_bytes(src.read())
            except RuntimeError as exc:  # zip con password
                raise ConversionError(f"l'archivio è protetto da password: {exc}") from exc
            ctx.log(f"Archivio: conversione di {member.filename}")
            try:
                text = finalize(extract(target, opts, ctx), opts)
            except ConversionError as exc:
                ctx.warn(f"{member.filename}: {exc}")
                continue
            if text.strip():
                paras.append(Para(f"File: {member.filename}", kind="heading"))
                paras.append(Para(text, kind="pre"))
    return Extracted(paras=paras)


BY_EXTENSION[".zip"] = extract_archive


def extract(path: Path, opts: Options, ctx: Context) -> Extracted:
    path = Path(path)
    if not path.is_file():
        raise ConversionError("il file non esiste o non è leggibile.")
    if path.stat().st_size == 0:
        raise ConversionError("il file è vuoto.")
    suffix = path.suffix.lower()
    if path.name.lower().endswith(".fb2.zip"):
        suffix = ".fb2"
    extractor = BY_EXTENSION.get(suffix) or _sniff(path)
    if extractor is None:
        raise ConversionError(f"formato del file non riconosciuto ({suffix or 'senza estensione'}).")
    return extractor(path, opts, ctx)


def supported_extensions() -> list[str]:
    return sorted(BY_EXTENSION)


def output_path(src: Path, opts: Options, taken: set | None = None) -> Path:
    """Nome del file di testo; ``taken`` evita che due file dello stesso lotto si sovrascrivano."""
    folder = Path(opts.output_dir) if opts.output_dir else src.parent
    name = src.stem + (" (testo).txt" if src.suffix.lower() == ".txt" else ".txt")
    target = folder / name
    if taken is not None:
        n = 1
        while str(target).lower() in taken:
            n += 1
            label = src.suffix.lstrip(".").lower() if n == 2 and src.suffix else str(n)
            target = folder / f"{src.stem} ({label}).txt"
        taken.add(str(target).lower())
    return target


def encode_text(text: str, encoding: str) -> bytes:
    if encoding.startswith("utf"):
        return text.encode(encoding)
    out = bytearray()
    for ch in text:
        try:
            out += ch.encode(encoding)
        except UnicodeEncodeError:
            simple = unicodedata.normalize("NFKD", ch).encode(encoding, "ignore")
            out += simple or b"?"
    return bytes(out)


def convert_file(src: Path, opts: Options, ctx: Context, taken: set | None = None) -> Path:
    """Converte ``src`` e scrive il file .txt. Restituisce il percorso del file creato."""
    src = Path(src)
    extracted = extract(src, opts, ctx)
    for warning in extracted.warnings:
        ctx.warn(warning)
    text = finalize(extracted, opts)
    if not text.strip():
        raise ConversionError("nel file non è stato trovato testo da salvare.")
    target = output_path(src, opts, taken)
    target.parent.mkdir(parents=True, exist_ok=True)
    if os.linesep != "\n":
        text = text.replace("\n", os.linesep)
    target.write_bytes(encode_text(text, opts.encoding))
    return target
