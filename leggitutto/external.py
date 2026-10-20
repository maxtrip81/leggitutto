"""Ricerca e uso di programmi esterni facoltativi (Tesseract, LibreOffice, Calibre...)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .settings import bundle_dir

_CANDIDATES = {
    "tesseract": {
        "win32": [r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                  os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe")],
        "darwin": ["/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract", "/opt/local/bin/tesseract"],
    },
    "soffice": {
        "win32": [r"C:\Program Files\LibreOffice\program\soffice.exe", r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"],
        "darwin": ["/Applications/LibreOffice.app/Contents/MacOS/soffice"],
    },
    "ebook-convert": {
        "win32": [r"C:\Program Files\Calibre2\ebook-convert.exe", r"C:\Program Files (x86)\Calibre2\ebook-convert.exe"],
        "darwin": ["/Applications/calibre.app/Contents/MacOS/ebook-convert"],
    },
    "djvutxt": {
        "win32": [r"C:\Program Files\DjVuLibre\djvutxt.exe", r"C:\Program Files (x86)\DjVuLibre\djvutxt.exe"],
        "darwin": ["/opt/homebrew/bin/djvutxt", "/usr/local/bin/djvutxt", "/Applications/DjView.app/Contents/bin/djvutxt"],
    },
    "textutil": {"darwin": ["/usr/bin/textutil"]},
}


def find_program(name: str) -> Optional[str]:
    """Cerca un programma: prima accanto all'app (versione inclusa), poi nel PATH, poi nei percorsi tipici."""
    exe = name + (".exe" if sys.platform == "win32" else "")
    base = bundle_dir()
    for folder in (base / name, base / "tools" / name, base / "tools", base):
        candidate = folder / exe
        if candidate.is_file():
            return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    for candidate in _CANDIDATES.get(name, {}).get(sys.platform, []):
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def run(args: list[str], timeout: int = 900) -> subprocess.CompletedProcess:
    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW: niente finestre nere
    return subprocess.run(args, capture_output=True, timeout=timeout, **kwargs)


def libreoffice_convert(src: Path, target_ext: str, out_dir: Path) -> Optional[Path]:
    soffice = find_program("soffice")
    if not soffice:
        return None
    profile = out_dir / "lo_profile"
    run([soffice, f"-env:UserInstallation={profile.as_uri()}", "--headless", "--norestore",
         "--convert-to", target_ext, "--outdir", str(out_dir), str(src)])
    result = out_dir / (src.stem + "." + target_ext.split(":")[0])
    return result if result.is_file() else None


def calibre_convert(src: Path, target_ext: str, out_dir: Path) -> Optional[Path]:
    tool = find_program("ebook-convert")
    if not tool:
        return None
    result = out_dir / (src.stem + "." + target_ext)
    run([tool, str(src), str(result)], timeout=1800)
    return result if result.is_file() else None
