"""Opzioni dell'utente e percorsi dell'applicazione."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from . import APP_NAME

WHISPER_MODELS = [
    ("tiny", "Minimo: velocissimo, qualità bassa (75 MB)"),
    ("base", "Base: veloce, qualità discreta (150 MB)"),
    ("small", "Medio: buon equilibrio (consigliato, 500 MB)"),
    ("medium", "Grande: qualità alta, lento (1,5 GB)"),
    ("large-v3-turbo", "Turbo: qualità molto alta, veloce sui computer recenti (1,6 GB)"),
    ("large-v3", "Massimo: qualità migliore, molto lento (3 GB)"),
]

LANGUAGES = [
    ("", "Riconoscimento automatico"),
    ("it", "Italiano"),
    ("en", "Inglese"),
    ("fr", "Francese"),
    ("de", "Tedesco"),
    ("es", "Spagnolo"),
    ("pt", "Portoghese"),
    ("nl", "Olandese"),
    ("ro", "Rumeno"),
    ("pl", "Polacco"),
    ("ru", "Russo"),
    ("uk", "Ucraino"),
    ("ar", "Arabo"),
    ("zh", "Cinese"),
    ("ja", "Giapponese"),
]

ENCODINGS = [
    ("utf-8", "UTF-8 (consigliata)"),
    ("utf-8-sig", "UTF-8 con BOM (per vecchi programmi Windows)"),
    ("cp1252", "ANSI Windows-1252 (per vecchi dispositivi braille)"),
]


@dataclass
class Options:
    # Pulizia dei documenti
    remove_page_numbers: bool = True
    remove_headers_footers: bool = True
    remove_footnotes: bool = True
    remove_note_markers: bool = True
    reflow_paragraphs: bool = True
    remove_decorations: bool = True
    include_slide_notes: bool = True
    ocr: bool = True
    ocr_languages: str = "ita+eng"
    # Audio e video
    whisper_model: str = "small"
    language: str = ""
    diarize: bool = True
    num_speakers: int = 0  # 0 = automatico
    timestamps: bool = False
    use_gpu: bool = False
    # Uscita
    encoding: str = "utf-8"
    wrap_width: int = 0  # 0 = nessun a capo forzato
    output_dir: str = ""  # vuoto = accanto al file originale
    # Interfaccia
    auto_convert_on_drop: bool = True
    open_when_done: bool = False

    @classmethod
    def load(cls) -> "Options":
        try:
            data = json.loads(settings_file().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        known = {f.name for f in fields(cls)}
        opts = cls()
        for key, value in data.items():
            if key in known and type(value) is type(getattr(opts, key)):
                setattr(opts, key, value)
        return opts

    def save(self):
        try:
            settings_file().write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        except OSError:
            pass


def app_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_file() -> Path:
    return app_data_dir() / "impostazioni.json"


def models_dir() -> Path:
    path = app_data_dir() / "modelli"
    path.mkdir(parents=True, exist_ok=True)
    return path


def bundle_dir() -> Path:
    """Cartella dell'eseguibile (o del progetto, se avviato da sorgente)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
