"""Uso da riga di comando: leggitutto --cli file1 file2 ... [opzioni]."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from .converter import convert_file
from .model import Cancelled, ConversionError, Context
from .settings import ENCODINGS, WHISPER_MODELS, Options


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="leggitutto --cli", description="Converte file di ogni tipo in testo .txt accessibile.")
    parser.add_argument("files", nargs="+", type=Path, help="file o cartelle da convertire")
    parser.add_argument("-o", "--output", help="cartella di destinazione (predefinita: accanto all'originale)")
    parser.add_argument("--password", help="password per i documenti protetti")
    parser.add_argument("--model", choices=[m for m, _ in WHISPER_MODELS], help="modello di riconoscimento vocale")
    parser.add_argument("--lang", help="lingua dell'audio, es. it, en (predefinita: automatica)")
    parser.add_argument("--speakers", type=int, help="numero di persone che parlano (0 = automatico)")
    parser.add_argument("--no-speakers", action="store_true", help="non distinguere le voci")
    parser.add_argument("--timestamps", action="store_true", help="aggiungi l'orario a ogni intervento")
    parser.add_argument("--keep-all", action="store_true", help="non togliere numeri di pagina, note, intestazioni")
    parser.add_argument("--encoding", choices=[e for e, _ in ENCODINGS])
    parser.add_argument("--wrap", type=int, help="va a capo ogni N caratteri (0 = mai)")
    args = parser.parse_args(argv)

    opts = Options.load()
    if args.output:
        opts.output_dir = args.output
    if args.model:
        opts.whisper_model = args.model
    if args.lang is not None:
        opts.language = args.lang
    if args.speakers is not None:
        opts.num_speakers = args.speakers
    if args.no_speakers:
        opts.diarize = False
    if args.timestamps:
        opts.timestamps = True
    if args.encoding:
        opts.encoding = args.encoding
    if args.wrap is not None:
        opts.wrap_width = args.wrap
    if args.keep_all:
        opts.remove_page_numbers = opts.remove_headers_footers = opts.remove_footnotes = False
        opts.remove_note_markers = opts.remove_decorations = False

    def ask_password(name, attempt):
        if args.password and attempt == 0:
            return args.password
        if not sys.stdin.isatty():
            return None
        return getpass.getpass(f"Password per {name}: ") or None

    def progress(fraction, message):
        if message and sys.stderr.isatty():
            print(f"\r  {int(fraction * 100):3d}% {message[:70]:<70}", end="", file=sys.stderr, flush=True)

    files: list[Path] = []
    for item in args.files:
        files.extend(sorted(p for p in item.rglob("*") if p.is_file()) if item.is_dir() else [item])

    errors = 0
    taken: set = set()
    for src in files:
        print(f"{src}:", file=sys.stderr)
        ctx = Context(progress=progress, ask_password=ask_password, log=lambda m: print("\n  " + m, file=sys.stderr))
        try:
            out = convert_file(src, opts, ctx, taken)
            print(f"\r  creato {out}".ljust(80), file=sys.stderr)
        except ConversionError as exc:
            errors += 1
            print(f"\r  errore: {exc}".ljust(80), file=sys.stderr)
        except Cancelled:
            return 130
    return 1 if errors else 0
