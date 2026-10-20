# -*- mode: python ; coding: utf-8 -*-
# Ricetta PyInstaller: crea LeggiTutto.exe (Windows) o LeggiTutto.app (macOS).
# Uso:  pyinstaller packaging/LeggiTutto.spec --noconfirm

import os
import sys

from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
sys.path.insert(0, ROOT)
from leggitutto import AUTHOR, AUTHOR_EMAIL, COPYRIGHT, __version__  # noqa: E402

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
# Dati dell'autore visibili in Windows (Proprietà del file > Dettagli).
version_info = None
if sys.platform == "win32":
    from PyInstaller.utils.win32.versioninfo import (FixedFileInfo, StringFileInfo, StringStruct, StringTable,
                                                     VarFileInfo, VarStruct, VSVersionInfo)

    numbers = tuple(int(n) for n in (__version__.split(".") + ["0", "0", "0"])[:4])
    version_info = VSVersionInfo(
        ffi=FixedFileInfo(filevers=numbers, prodvers=numbers),
        kids=[
            StringFileInfo([StringTable("041004B0", [
                StringStruct("CompanyName", AUTHOR),
                StringStruct("FileDescription", "LeggiTutto - convertitore accessibile in testo"),
                StringStruct("FileVersion", __version__),
                StringStruct("InternalName", "LeggiTutto"),
                StringStruct("LegalCopyright", f"{COPYRIGHT} - {AUTHOR_EMAIL}"),
                StringStruct("OriginalFilename", "LeggiTutto.exe"),
                StringStruct("ProductName", "LeggiTutto"),
                StringStruct("ProductVersion", __version__),
            ])]),
            VarFileInfo([VarStruct("Translation", [0x0410, 1200])]),
        ],
    )

# Firma per macOS: se è impostata l'identità "Developer ID Application", PyInstaller firma
# ogni file con il runtime protetto richiesto dalla notarizzazione Apple.
mac_identity = os.environ.get("MACOS_SIGN_IDENTITY") or None
mac_entitlements = os.path.join(SPECPATH, "entitlements.plist") if mac_identity else None

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LeggiTutto",
    console=False,
    icon=None,
    version=version_info,
    codesign_identity=mac_identity,
    entitlements_file=mac_entitlements,
)
coll = COLLECT(exe, a.binaries, a.datas, name="LeggiTutto")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        codesign_identity=mac_identity,
        entitlements_file=mac_entitlements,
        name="LeggiTutto.app",
        bundle_identifier="it.leggitutto.convertitore",
        version=__version__,
        info_plist={
            "CFBundleDisplayName": "LeggiTutto",
            "CFBundleDevelopmentRegion": "it",
            "CFBundleLocalizations": ["it", "en"],
            "NSHumanReadableCopyright": f"{COPYRIGHT} - {AUTHOR_EMAIL}",
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
