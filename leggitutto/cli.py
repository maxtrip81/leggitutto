"""Uso da riga di comando: leggitutto --cli file1 file2 ... [opzioni]."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from .converter import convert_file
from .i18n import _, set_language
from .model import Cancelled, ConversionError, Context
from .settings import ENCODINGS, UI_LANGUAGES, WHISPER_MODELS, Options


def main(argv: list[str]) -> int:
    opts = Options.load()
    # La lingua va decisa prima di costruire i testi di aiuto.
    if "--ui" in argv[:-1]:
        opts.ui_language = argv[argv.index("--ui") + 1]
    set_language(opts.ui_language)

    parser = argparse.ArgumentParser(prog="leggitutto --cli",
                                     description=_("Converte file di ogni tipo in testo .txt accessibile."))
    parser.add_argument("files", nargs="+", type=Path, help=_("file o cartelle da convertire"))
    parser.add_argument("-o", "--output", help=_("cartella di destinazione (predefinita: accanto all'originale)"))
    parser.add_argument("--password", help=_("password per i documenti protetti"))
    parser.add_argument("--model", choices=[m for m, _d in WHISPER_MODELS], help=_("modello di riconoscimento vocale"))
    parser.add_argument("--lang", help=_("lingua dell'audio, es. it, en (predefinita: automatica)"))
    parser.add_argument("--speakers", type=int, help=_("numero di persone che parlano (0 = automatico)"))
    parser.add_argument("--no-speakers", action="store_true", help=_("non distinguere le voci"))
    parser.add_argument("--timestamps", action="store_true", help=_("aggiungi l'orario a ogni intervento"))
    parser.add_argument("--keep-all", action="store_true", help=_("non togliere numeri di pagina, note, intestazioni"))
    parser.add_argument("--encoding", choices=[e for e, _d in ENCODINGS])
    parser.add_argument("--wrap", type=int, help=_("va a capo ogni N caratteri (0 = mai)"))
    parser.add_argument("--ui", choices=[c for c, _d in UI_LANGUAGES], help=_("lingua dei messaggi (it, en)"))
    args = parser.parse_args(argv)

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
        return getpass.getpass(_("Password per {name}: ").format(name=name)) or None

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
            print(("\r  " + _("creato {path}").format(path=out)).ljust(80), file=sys.stderr)
        except ConversionError as exc:
            errors += 1
            print(("\r  " + _("errore: {exc}").format(exc=exc)).ljust(80), file=sys.stderr)
        except Cancelled:
            return 130
    return 1 if errors else 0
