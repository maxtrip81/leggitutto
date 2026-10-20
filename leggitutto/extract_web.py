"""Pagine web, eBook (ePub, FB2, MOBI...), Markdown, sottotitoli e testo semplice."""

from __future__ import annotations

import json
import posixpath
import re
import tempfile
import warnings
import zipfile
from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

try:
    from bs4 import XMLParsedAsHTMLWarning

    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:
    pass
from lxml import etree

from . import external
from .cleaner import reflow_plain_text
from .extract_office import table_to_paras
from .i18n import _
from .model import ConversionError, Context, Extracted, Para, ProtectedError
from .settings import Options

def drm_message() -> str:
    return _(DRM_MESSAGE)


DRM_MESSAGE = (
    "il libro è protetto da DRM (blocco anticopia dell'editore). LeggiTutto non rimuove i DRM: "
    "puoi chiedere una copia accessibile all'editore, alla tua biblioteca o ai servizi per persone "
    "con disabilità visiva (in Italia ad esempio la Biblioteca Italiana per i Ciechi o il Libro Parlato), "
    "che possono fornirla grazie al Trattato di Marrakech."
)


# ---------------------------------------------------------------------------
# Lettura di file di testo con qualsiasi codifica

def decode_bytes(data: bytes) -> str:
    for bom, enc in ((b"\xef\xbb\xbf", "utf-8-sig"), (b"\xff\xfe", "utf-16"), (b"\xfe\xff", "utf-16")):
        if data.startswith(bom):
            return data.decode(enc, errors="replace")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    # I vecchi file di testo italiani sono quasi sempre in Windows-1252: la proviamo per prima,
    # a meno che non compaiano i caratteri grafici tipici dei file DOS (cp850).
    try:
        text = data.decode("cp1252")
        if sum(1 for b in data if 0xB0 <= b <= 0xDF and b not in (0xC0, 0xC8, 0xC9, 0xCC, 0xD2, 0xD9)) < len(data) * 0.01:
            return text
    except UnicodeDecodeError:
        pass
    try:
        from charset_normalizer import from_bytes

        best = from_bytes(data[:200000]).best()
        if best is not None:
            return data.decode(best.encoding, errors="replace")
    except Exception:
        pass
    return data.decode("cp1252", errors="replace")


def read_text_file(path: Path) -> str:
    return decode_bytes(path.read_bytes())


# ---------------------------------------------------------------------------
# HTML -> paragrafi

_BLOCK_TAGS = {
    "p", "div", "section", "article", "main", "li", "blockquote", "dd", "dt", "dl", "ul", "ol",
    "figcaption", "figure", "caption", "header", "footer", "aside", "nav", "address", "center",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "body", "html", "tr", "td", "th", "form", "fieldset",
    "legend", "details", "summary", "hgroup", "title",
}
_SKIP_TAGS = {"script", "style", "noscript", "template", "head", "svg", "math", "object", "embed", "iframe",
              "canvas", "audio", "video", "map", "button", "select", "input", "textarea", "rp"}
_WEB_JUNK_TAGS = {"nav", "header", "footer", "aside", "form", "menu", "dialog"}
_WEB_JUNK_ROLES = {"navigation", "banner", "contentinfo", "complementary", "search", "menu", "menubar", "dialog", "alert"}
_NOTE_TYPES = {"footnote", "footnotes", "endnote", "endnotes", "rearnote", "rearnotes", "note", "annotation"}
_NOTEREF_TEXT_RE = re.compile(r"^[\[(]?\s*(?:\d{1,3}|[*†‡§]+|[ivx]{1,4}|[a-z])\s*[\])]?$", re.I)


def _attr_words(tag: Tag, name: str) -> set[str]:
    value = tag.get(name)
    if isinstance(value, list):
        value = " ".join(value)
    return set((value or "").lower().split())


def _types(tag: Tag) -> set[str]:
    return _attr_words(tag, "epub:type") | {r.replace("doc-", "") for r in _attr_words(tag, "role")}


def _is_noteref(tag: Tag) -> bool:
    if tag.name not in ("a", "sup", "span"):
        return False
    types = _types(tag)
    if "noteref" in types or "biblioref" in types:
        return True
    classes = _attr_words(tag, "class")
    if classes & {"footnote-ref", "footnoteref", "noteref", "fnref", "endnote-ref", "mw-ref", "reference"}:
        return True
    text = tag.get_text(strip=True)
    if tag.name == "a" and "#" in (tag.get("href") or "") and _NOTEREF_TEXT_RE.match(text or "x"):
        return tag.find_parent("sup") is not None or bool(re.match(r"^\[?\d", text)) or "note" in (tag.get("href") or "").lower() or "fn" in (tag.get("href") or "").lower()
    if tag.name == "sup":
        link = tag.find("a")
        return link is not None and "#" in (link.get("href") or "") and _NOTEREF_TEXT_RE.match(text or "x") is not None
    return False


def _is_note_body(tag: Tag) -> bool:
    if _types(tag) & _NOTE_TYPES:
        return True
    style = (tag.get("style") or "").replace(" ", "").lower()
    if "mso-element:footnote" in style or "mso-element:endnote" in style:
        return True
    classes = _attr_words(tag, "class") | _attr_words(tag, "id")
    return tag.name in ("div", "section", "ol", "aside", "ul") and bool(classes & {"footnotes", "endnotes", "notes", "footnote", "endnote", "references", "reflist"})


def _is_pagebreak(tag: Tag) -> bool:
    if "pagebreak" in _types(tag):
        return True
    classes = _attr_words(tag, "class")
    return tag.name in ("span", "div", "a", "p") and bool(classes & {"pagebreak", "page-break", "pagenum", "page-number", "pagenumber", "page_number"})


def find_noterefs(soup: BeautifulSoup, doc_name: str = "") -> tuple[list[Tag], set[str]]:
    """Trova i richiami di nota e gli identificativi ("file#id") delle note a cui rimandano."""
    refs = list(soup.find_all(_is_noteref))
    targets: set[str] = set()
    for tag in refs:
        link = tag if tag.name == "a" else tag.find("a")
        href = (link.get("href") if link is not None else "") or ""
        if "#" in href:
            file_part, frag = href.split("#", 1)
            if file_part:
                file_part = posixpath.normpath(posixpath.join(posixpath.dirname(doc_name), unquote(file_part)))
            else:
                file_part = doc_name
            targets.add(f"{file_part}#{unquote(frag)}")
    return refs, targets


def _text_before(block: Tag, target: Tag) -> str:
    parts = []
    for node in block.descendants:
        if node is target:
            break
        if isinstance(node, NavigableString) and not isinstance(node, Comment):
            parts.append(str(node))
    return "".join(parts)


def remove_notes(soup: BeautifulSoup, opts: Options, ids: set[str], refs: list[Tag]):
    """Toglie i testi delle note (prima) e i richiami nel testo (dopo)."""
    if opts.remove_footnotes:
        for tag in list(soup.find_all(_is_note_body)):
            tag.decompose()
        for note_id in ids:
            el = soup.find(id=note_id) or soup.find(attrs={"name": note_id})
            if el is None:
                continue
            block = el
            if el.name in ("a", "span", "sup"):
                block = el.find_parent(["p", "li", "aside", "div", "dd"]) or el
            if block.name in ("body", "html", "section") or len(block.get_text()) > 3000:
                continue
            # Una nota comincia con il suo numero; se l'ancora è a metà del paragrafo, quello è
            # il testo principale (è il "torna al testo" della nota a puntare lì).
            if block is not el and len(_text_before(block, el).strip()) > 3:
                continue
            block.decompose()
    if opts.remove_note_markers or opts.remove_footnotes:
        for tag in refs:
            if getattr(tag, "decomposed", False):
                continue
            parent = tag.parent
            tag.decompose()
            if parent is not None and parent.name == "sup" and not parent.get_text(strip=True):
                parent.decompose()
    if opts.remove_page_numbers:
        for tag in list(soup.find_all(_is_pagebreak)):
            tag.decompose()


def _strip_notes_single(soup: BeautifulSoup, opts: Options):
    refs, targets = find_noterefs(soup)
    remove_notes(soup, opts, {t.split("#", 1)[1] for t in targets}, refs)


def _clean_web_page(soup: BeautifulSoup):
    """Modalità lettura: tiene solo il contenuto principale di una pagina web."""
    for tag in list(soup.find_all(True)):
        if getattr(tag, "decomposed", False):
            continue
        style = (tag.get("style") or "").replace(" ", "").lower()
        if (tag.name in _WEB_JUNK_TAGS or _attr_words(tag, "role") & _WEB_JUNK_ROLES or tag.get("aria-hidden") == "true"
                or tag.get("hidden") is not None or (tag.name == "div" and tag.get("title") in ("header", "footer"))
                or "mso-element:header" in style or "mso-element:footer" in style):
            tag.decompose()
    main = soup.find("main") or soup.find(attrs={"role": "main"})
    articles = soup.find_all("article")
    if main is None and len(articles) == 1:
        main = articles[0]
    return main or soup.body or soup


def html_to_paras(root, opts: Options) -> list[Para]:
    paras: list[Para] = []
    buffer: list[str] = []

    def flush(kind="text"):
        text = "".join(buffer)
        buffer.clear()
        text = re.sub(r"[ \t\r\f\v]+", " ", text.replace("\xa0", " "))
        text = re.sub(r" *\n *", "\n", text).strip()
        if text:
            paras.append(Para(text, kind=kind))

    def walk(node):
        for child in node.children:
            if isinstance(child, Comment):
                continue
            if isinstance(child, NavigableString):
                if type(child).__name__ in ("CData", "ProcessingInstruction", "Declaration", "Doctype"):
                    continue
                buffer.append(str(child).replace("\n", " "))
                continue
            if not isinstance(child, Tag):
                continue
            name = (child.name or "").lower().split(":")[-1]
            if name in _SKIP_TAGS or child.get("hidden") is not None:
                continue
            if name == "br":
                buffer.append("\n")
            elif name == "img":
                alt = (child.get("alt") or "").strip()
                if len(alt) > 3 and not re.search(r"\.(jpe?g|png|gif|svg|webp)$", alt, re.I):
                    buffer.append(" [%s] " % _("Immagine: {alt}").format(alt=alt))
            elif name == "table":
                flush()
                rows = []
                for tr in child.find_all("tr"):
                    if tr.find_parent("table") is child:
                        rows.append([c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"], recursive=False)])
                caption = child.find("caption")
                if caption is not None and caption.get_text(strip=True):
                    paras.append(Para(caption.get_text(" ", strip=True)))
                paras.extend(table_to_paras(rows))
            elif name == "pre":
                flush()
                text = child.get_text()
                if text.strip():
                    paras.append(Para(text, kind="pre"))
            elif name in _BLOCK_TAGS:
                flush()
                walk(child)
                kind = "heading" if re.match(r"h[1-6]$", name) else "list" if name == "li" else "text"
                flush(kind)
            else:
                walk(child)

    walk(root)
    flush()
    return paras


def _soup(data: bytes | str) -> BeautifulSoup:
    if isinstance(data, bytes):
        data = decode_bytes(data)
    return BeautifulSoup(data, "lxml")


def extract_html(path: Path, opts: Options, ctx: Context) -> Extracted:
    soup = _soup(path.read_bytes())
    _strip_notes_single(soup, opts)
    root = _clean_web_page(soup) if opts.remove_decorations else (soup.body or soup)
    return Extracted(paras=html_to_paras(root, opts))


def extract_mht(path: Path, opts: Options, ctx: Context) -> Extracted:
    import email
    from email import policy

    msg = email.message_from_bytes(path.read_bytes(), policy=policy.default)
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            soup = _soup(part.get_content())
            _strip_notes_single(soup, opts)
            return Extracted(paras=html_to_paras(_clean_web_page(soup), opts))
    raise ConversionError(_("l'archivio web non contiene una pagina leggibile."))


# ---------------------------------------------------------------------------
# ePub

_FONT_OBFUSCATION = {"http://www.idpf.org/2008/embedding", "http://ns.adobe.com/pdf/enc#RC"}


def check_epub_drm(zf: zipfile.ZipFile):
    names = set(zf.namelist())
    if "META-INF/rights.xml" in names or "META-INF/sinf.xml" in names:
        raise ProtectedError(drm_message())
    if "META-INF/encryption.xml" in names:
        root = etree.fromstring(zf.read("META-INF/encryption.xml"))
        for data in root.iter("{http://www.w3.org/2001/04/xmlenc#}EncryptedData"):
            method = data.find("{http://www.w3.org/2001/04/xmlenc#}EncryptionMethod")
            ref = data.find(".//{http://www.w3.org/2001/04/xmlenc#}CipherReference")
            algo = method.get("Algorithm", "") if method is not None else ""
            uri = (ref.get("URI", "") if ref is not None else "").lower()
            if algo not in _FONT_OBFUSCATION and not uri.endswith((".ttf", ".otf", ".woff", ".woff2")):
                raise ProtectedError(drm_message())


def extract_epub(path: Path, opts: Options, ctx: Context) -> Extracted:
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise ConversionError(_("ePub non valido: {exc}").format(exc=exc)) from exc
    with zf:
        check_epub_drm(zf)
        container = etree.fromstring(zf.read("META-INF/container.xml"))
        opf_path = container.find(".//{*}rootfile").get("full-path")
        opf = etree.fromstring(zf.read(opf_path))
        base = posixpath.dirname(opf_path)
        manifest = {}
        for item in opf.iter("{*}item"):
            href = posixpath.normpath(posixpath.join(base, unquote(item.get("href", ""))))
            manifest[item.get("id")] = (href, item.get("media-type", ""), item.get("properties", ""))
        spine = [ref.get("idref") for ref in opf.iter("{*}itemref")]
        docs = []
        for idref in spine:
            if idref not in manifest:
                continue
            href, media, props = manifest[idref]
            if "nav" in props.split() and opts.remove_decorations:
                continue
            if "html" not in media and not href.lower().endswith((".htm", ".html", ".xhtml")):
                continue
            try:
                docs.append((href, _soup(zf.read(href))))
            except KeyError:
                continue

    targets: set[str] = set()
    refs_by_doc = {}
    for name, soup in docs:
        refs_by_doc[name], found = find_noterefs(soup, name)
        targets |= found
    paras: list[Para] = []
    for n, (name, soup) in enumerate(docs):
        ctx.progress(n / max(len(docs), 1), _("Capitolo {n} di {total}").format(n=n + 1, total=len(docs)))
        ids = {t.split("#", 1)[1] for t in targets if t.split("#", 1)[0] == name}
        remove_notes(soup, opts, ids, refs_by_doc[name])
        paras.extend(html_to_paras(soup.body or soup, opts))
    return Extracted(paras=paras)


# ---------------------------------------------------------------------------
# FictionBook (.fb2, .fb2.zip)

def extract_fb2(path: Path, opts: Options, ctx: Context) -> Extracted:
    data = path.read_bytes()
    if data[:2] == b"PK":
        with zipfile.ZipFile(path) as zf:
            name = next((n for n in zf.namelist() if n.lower().endswith(".fb2")), None)
            if not name:
                raise ConversionError(_("l'archivio non contiene un libro FB2."))
            data = zf.read(name)
    root = etree.fromstring(data, etree.XMLParser(recover=True, huge_tree=True))
    paras: list[Para] = []

    def text_of(el):
        parts = [el.text or ""]
        for child in el:
            local = etree.QName(child).localname
            is_note = local == "a" and (child.get("type") == "note")
            if not (is_note and opts.remove_note_markers):
                parts.append(text_of(child))
            parts.append(child.tail or "")
        return "".join(parts)

    def walk(el):
        for child in el:
            local = etree.QName(child).localname
            if local in ("p", "v", "subtitle", "text-author"):
                paras.append(Para(text_of(child), kind="heading" if local == "subtitle" else "text"))
            elif local == "title":
                paras.append(Para(" ".join(text_of(p) for p in child), kind="heading"))
            elif local == "table":
                rows = [[text_of(c) for c in tr] for tr in child]
                paras.extend(table_to_paras(rows))
            elif local in ("section", "poem", "stanza", "cite", "epigraph", "annotation"):
                walk(child)

    for body in root.iter("{*}body"):
        if body.get("name") in ("notes", "comments") and opts.remove_footnotes:
            continue
        walk(body)
    return Extracted(paras=paras)


# ---------------------------------------------------------------------------
# MOBI, AZW, DjVu e altri eBook

def extract_ebook_other(path: Path, opts: Options, ctx: Context) -> Extracted:
    from .converter import extract
    from .extract_pdf import extract_pdf

    with open(path, "rb") as fh:
        head = fh.read(65536)
    if len(head) > 86 and head[60:68] in (b"BOOKMOBI", b"TEXtREAd"):
        # Campo "encryption" del primo record MOBI/PalmDOC: 0 = nessun DRM.
        first_record = int.from_bytes(head[78:82], "big")
        if len(head) >= first_record + 14 and int.from_bytes(head[first_record + 12:first_record + 14], "big") != 0:
            raise ProtectedError(drm_message())
    if path.suffix.lower() in (".kfx", ".azw4", ".azw8", ".kfx-zip"):
        raise ProtectedError(drm_message())

    with tempfile.TemporaryDirectory() as tmp:
        if path.suffix.lower() == ".djvu" or path.suffix.lower() == ".djv":
            tool = external.find_program("djvutxt")
            if tool:
                out = Path(tmp) / "testo.txt"
                external.run([tool, str(path), str(out)])
                if out.is_file():
                    return extract_plain_text(out, opts, ctx)
        converted = None
        try:
            converted = external.calibre_convert(path, "epub", Path(tmp))
        except Exception as exc:
            ctx.log(_("Calibre non è riuscito a convertire il file: {exc}").format(exc=exc))
        if converted is not None:
            return extract(converted, opts, ctx)
        try:
            import mobi  # type: ignore

            tempdir, filepath = mobi.extract(str(path))
            return extract(Path(filepath), opts, ctx)
        except Exception:
            pass
    try:
        return extract_pdf(path, opts, ctx, filetype=path.suffix.lower().lstrip(".") or None)
    except ProtectedError:
        raise
    except Exception:
        raise ConversionError(_(
            "per i file {ext} serve Calibre (gratuito, calibre-ebook.com): installalo e riprova.").format(ext=path.suffix))


# ---------------------------------------------------------------------------
# Testo semplice, Markdown, sottotitoli, XML, JSON

def extract_plain_text(path: Path, opts: Options, ctx: Context) -> Extracted:
    text = read_text_file(path)
    if "\f" in text:
        pages = []
        for chunk in text.split("\f"):
            paras = reflow_plain_text(chunk) if opts.reflow_paragraphs else [Para(l) for l in chunk.split("\n")]
            paras = [p for p in paras if p.text.strip()]
            if paras and len(paras[0].text) < 80:
                paras[0].zone = "top"
            if len(paras) > 1 and len(paras[-1].text) < 80:
                paras[-1].zone = "bottom"
            pages.append(paras)
        return Extracted(pages=pages)
    if opts.reflow_paragraphs:
        return Extracted(paras=reflow_plain_text(text))
    return Extracted(paras=[Para(l) for l in text.split("\n")])


def extract_markdown(path: Path, opts: Options, ctx: Context) -> Extracted:
    text = read_text_file(path)
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)  # intestazione YAML
    paras: list[Para] = []
    lines = text.split("\n")
    i = 0
    buf: list[str] = []

    def flush():
        if buf:
            paras.extend(reflow_plain_text("\n".join(buf)) if opts.reflow_paragraphs else [Para(" ".join(buf))])
            buf.clear()

    def inline(s: str) -> str:
        s = re.sub(r"!\[([^\]]*)\]\([^)]*\)", lambda m: "[%s]" % _("Immagine: {alt}").format(alt=m.group(1)) if m.group(1) else "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
        s = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", s)
        s = re.sub(r"<[^>]+>", "", s)
        s = re.sub(r"(\*\*|__)(.+?)\1", r"\2", s)
        s = re.sub(r"(?<![\w*])([*_])(?!\s)(.+?)(?<!\s)\1(?![\w*])", r"\2", s)
        s = re.sub(r"~~(.+?)~~", r"\1", s)
        s = re.sub(r"`([^`]+)`", r"\1", s)
        return s

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            flush()
            fence = stripped[:3]
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(fence):
                code.append(lines[i])
                i += 1
            paras.append(Para("\n".join(code), kind="pre"))
        elif re.match(r"^#{1,6}\s", stripped):
            flush()
            paras.append(Para(inline(stripped.lstrip("#").strip().rstrip("#").strip()), kind="heading"))
        elif re.match(r"^\[\^[^\]]+\]:", stripped):
            flush()
            if not opts.remove_footnotes:
                paras.append(Para(inline(re.sub(r"^\[\^[^\]]+\]:\s*", "", stripped))))
        elif re.match(r"^\[[^\]]+\]:\s*\S+", stripped):
            pass  # definizione di collegamento
        elif stripped.startswith("|") and stripped.endswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [inline(c.strip()) for c in lines[i].strip().strip("|").split("|")]
                if not all(re.match(r"^:?-{2,}:?$", c) for c in row if c):
                    rows.append(row)
                i += 1
            paras.extend(table_to_paras(rows))
            continue
        elif re.match(r"^(\*\s*){3,}$|^(-\s*){3,}$|^(_\s*){3,}$", stripped):
            flush()
        elif not stripped:
            flush()
        else:
            stripped = re.sub(r"^>\s?", "", stripped)
            if re.match(r"^([-*+]|\d+[.)])\s", stripped):
                flush()
                stripped = re.sub(r"^[-*+]\s", "• ", stripped)
            buf.append(inline(stripped))
        i += 1
    flush()
    return Extracted(paras=paras)


_TIME_RE = re.compile(r"(\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{1,3}")


def _seconds(stamp: str) -> float:
    parts = stamp.replace(",", ".").split(":")
    return sum(float(p) * 60 ** i for i, p in enumerate(reversed(parts)))


def extract_subtitles(path: Path, opts: Options, ctx: Context) -> Extracted:
    text = read_text_file(path)
    cues: list[tuple[float, float, str]] = []
    if path.suffix.lower() in (".ass", ".ssa"):
        for line in text.split("\n"):
            if line.startswith("Dialogue:"):
                fields = line.split(",", 9)
                if len(fields) == 10:
                    content = re.sub(r"\{[^}]*\}", "", fields[9]).replace("\\N", " ").replace("\\n", " ")
                    cues.append((_seconds(fields[1]), _seconds(fields[2]), content))
    else:
        for block in re.split(r"\n\s*\n", text.replace("\r", "")):
            lines = [l for l in block.split("\n") if l.strip()]
            for j, line in enumerate(lines):
                if "-->" in line:
                    times = [m.group(0) for m in _TIME_RE.finditer(line)]
                    start = _seconds(times[0]) if times else 0.0
                    end = _seconds(times[1]) if times and len(times) > 1 else start
                    content = " ".join(lines[j + 1:])
                    content = re.sub(r"<v\s+([^>]+)>", r"\1: ", content)
                    content = re.sub(r"<[^>]+>|\{[^}]*\}", "", content)
                    cues.append((start, end, content.strip()))
                    break
    paras: list[str] = []
    last_end = -10.0
    last_text = ""
    for start, end, content in cues:
        content = re.sub(r"\s+", " ", content).strip()
        if not content or content == last_text:
            continue
        # I sottotitoli automatici ripetono la riga precedente: la togliamo.
        if last_text and content.startswith(last_text):
            content = content[len(last_text):].strip()
        if not content:
            continue
        if not paras or start - last_end > 2.5 or re.match(r"^[-–]\s|^[A-Z][\w ]{0,25}:\s", content):
            paras.append(content.lstrip("-– "))
        else:
            paras[-1] += " " + content
        last_end, last_text = end, content
    return Extracted(paras=[Para(p) for p in paras])


def extract_xml(path: Path, opts: Options, ctx: Context) -> Extracted:
    data = path.read_bytes()
    try:
        root = etree.fromstring(data, etree.XMLParser(recover=True, huge_tree=True))
    except etree.XMLSyntaxError:
        root = None
    if root is None:
        return extract_plain_text(path, opts, ctx)
    if etree.QName(root).localname.lower() == "html":
        return extract_html(path, opts, ctx)
    paras = []
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        text = (el.text or "").strip()
        if text:
            paras.append(Para(text))
    return Extracted(paras=paras)


def extract_json(path: Path, opts: Options, ctx: Context) -> Extracted:
    try:
        data = json.loads(read_text_file(path))
    except ValueError:
        return extract_plain_text(path, opts, ctx)
    paras: list[Para] = []

    def walk(value, label=""):
        if isinstance(value, dict):
            for key, sub in value.items():
                walk(sub, str(key))
        elif isinstance(value, list):
            for sub in value:
                walk(sub, label)
        elif value is not None and str(value).strip():
            paras.append(Para(f"{label}: {value}" if label else str(value)))

    walk(data)
    return Extracted(paras=paras)
