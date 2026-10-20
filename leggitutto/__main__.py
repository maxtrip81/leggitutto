"""Avvio: senza argomenti apre la finestra; con --cli lavora da riga di comando."""

import multiprocessing
import os
import sys


def main():
    multiprocessing.freeze_support()
    # Nelle app "a finestra" (senza console) stdout/stderr non esistono: alcune librerie ci scrivono.
    for name in ("stdout", "stderr"):
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        from .cli import main as cli_main

        sys.exit(cli_main(sys.argv[2:]))
    from .app import main as gui_main

    gui_main([a for a in sys.argv[1:] if not a.startswith("-psn_")])


if __name__ == "__main__":
    main()
