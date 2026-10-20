"""Ogni testo dell'interfaccia deve avere la traduzione inglese, con gli stessi segnaposto."""

import ast
import string
from pathlib import Path

from leggitutto import i18n, settings
from leggitutto.extract_web import DRM_MESSAGE

PACKAGE = Path(__file__).resolve().parent.parent / "leggitutto"


def translatable_strings():
    found = set()
    for path in PACKAGE.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("_", "ngettext"):
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        found.add(arg.value)
    for table in (settings.WHISPER_MODELS, settings.LANGUAGES, settings.ENCODINGS):
        found.update(label for _code, label in table)
    found.add(DRM_MESSAGE)
    return found


def fields(text):
    return {name for _lit, name, _spec, _conv in string.Formatter().parse(text) if name}


def test_every_string_is_translated():
    missing = sorted(t for t in translatable_strings() if t not in i18n.EN)
    assert not missing, "Traduzioni mancanti:\n" + "\n".join(missing)


def test_placeholders_match():
    for it, en in list(i18n.EN.items()) + list(i18n.EN_ONE.items()):
        assert fields(it) == fields(en), it


def test_switching_language():
    from leggitutto.media import _duration_words

    try:
        i18n.set_language("en")
        assert i18n._("Persona {n}").format(n=2) == "Speaker 2"
        assert _duration_words(3725) == "1 hour, 2 minutes and 5 seconds"
        assert i18n.ngettext(1, "{n} file convertito.", "{n} file convertiti.").format(n=1) == "1 file converted."
        i18n.set_language("it")
        assert _duration_words(3725) == "1 ora, 2 minuti e 5 secondi"
    finally:
        i18n.set_language("it")
