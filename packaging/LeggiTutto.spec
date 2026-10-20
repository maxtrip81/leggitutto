# -*- mode: python ; coding: utf-8 -*-
# Ricetta PyInstaller: crea LeggiTutto.exe (Windows) o LeggiTutto.app (macOS).
# Uso:  pyinstaller packaging/LeggiTutto.spec --noconfirm

import os
import sys

from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
sys.path.insert(0, ROOT)
from leggitutto import __version__  # noqa: E402

datas, binaries, hiddenimports = [], [], []
packages = ["faster_whisper", "ctranslate2", "sherpa_onnx", "onnxruntime", "pymupdf", "av", "tokenizers",
            "docx", "pptx", "msoffcrypto", "mobi", "charset_normalizer"]
if sys.platform == "win32":
    packages += ["accessible_output2", "libloader", "platform_utils"]
for package in packages:
    try:
        d, b, h = collect_all(package)
    except Exception:
        continue
    datas += d
    binaries += b
    hiddenimports += h

# Tesseract incluso nell'installazione (facoltativo): mettilo in packaging/tesseract prima di compilare.
tess_dir = os.path.join(SPECPATH, "tesseract")
if os.path.isdir(tess_dir):
    datas.append((tess_dir, "tesseract"))

a = Analysis(
    [os.path.join(ROOT, "LeggiTutto.py")],
    pathex=[ROOT],
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports + ["leggitutto.app", "leggitutto.cli"],
    excludes=["torch", "tensorflow", "tkinter", "matplotlib", "IPython", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LeggiTutto",
    console=False,
    icon=None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="LeggiTutto")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="LeggiTutto.app",
        bundle_identifier="it.leggitutto.convertitore",
        version=__version__,
        info_plist={
            "CFBundleDisplayName": "LeggiTutto",
            "CFBundleShortVersionString": __version__,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            # Permette di trascinare qualsiasi file sull'icona dell'app (Dock o Finder).
            "CFBundleDocumentTypes": [{
                "CFBundleTypeName": "Qualsiasi file",
                "CFBundleTypeRole": "Viewer",
                "LSHandlerRank": "Alternate",
                "LSItemContentTypes": ["public.item", "public.data", "public.content"],
            }],
        },
    )
