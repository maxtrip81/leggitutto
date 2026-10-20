"""Strutture dati condivise da tutti gli estrattori."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable, Optional


class ConversionError(Exception):
    """Errore con un messaggio comprensibile per l'utente."""


class ProtectedError(ConversionError):
    """Il file è protetto e non può essere aperto."""


class Cancelled(Exception):
    """L'utente ha interrotto la conversione."""


@dataclass
class Line:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    size: float
    bold: bool = False


@dataclass
class Block:
    """Un blocco di testo posizionato su una pagina (PDF o OCR)."""

    lines: list[Line]
    raw_start: str = ""  # testo grezzo iniziale, prima di togliere i richiami di nota
    table: Optional[list["Para"]] = None  # tabella già convertita in paragrafi

    @property
    def x0(self):
        return min(ln.x0 for ln in self.lines)

    @property
    def x1(self):
        return max(ln.x1 for ln in self.lines)

    @property
    def y0(self):
        return min(ln.y0 for ln in self.lines)

    @property
    def y1(self):
        return max(ln.y1 for ln in self.lines)

    @property
    def size(self):
        chars = sum(len(ln.text) for ln in self.lines) or 1
        return sum(ln.size * len(ln.text) for ln in self.lines) / chars

    @property
    def text(self):
        return " ".join(ln.text for ln in self.lines)


@dataclass
class Para:
    text: str
    zone: str = "body"  # "top", "bottom" o "body"
    kind: str = "text"  # "text", "heading", "list", "pre"


@dataclass
class Extracted:
    """Risultato grezzo di un estrattore.

    - ``pages``: documento impaginato (PDF, immagini): lista di pagine, ognuna
      lista di paragrafi. Consente di riconoscere intestazioni ripetute ecc.
    - ``paras``: documento a flusso (Word, ePub, HTML...).
    - ``final``: testo già pronto (es. trascrizioni), solo rifinitura minima.
    """

    pages: Optional[list[list[Para]]] = None
    paras: Optional[list[Para]] = None
    final: Optional[str] = None
    warnings: list[str] = field(default_factory=list)


class Context:
    """Canale fra il motore di conversione e l'interfaccia."""

    def __init__(
        self,
        progress: Optional[Callable[[float, str], None]] = None,
        ask_password: Optional[Callable[[str, int], Optional[str]]] = None,
        log: Optional[Callable[[str], None]] = None,
        cancel_event: Optional[threading.Event] = None,
    ):
        self._progress = progress
        self._ask_password = ask_password
        self._log = log
        self.cancel_event = cancel_event or threading.Event()
        self.warnings: list[str] = []

    def progress(self, fraction: float, message: str = ""):
        self.check_cancel()
        if self._progress:
            self._progress(max(0.0, min(1.0, fraction)), message)

    def log(self, message: str):
        if self._log:
            self._log(message)

    def warn(self, message: str):
        if message not in self.warnings:
            self.warnings.append(message)
            self.log("Attenzione: " + message)

    def ask_password(self, filename: str, attempt: int) -> Optional[str]:
        if self._ask_password is None:
            return None
        return self._ask_password(filename, attempt)

    def check_cancel(self):
        if self.cancel_event.is_set():
            raise Cancelled()
