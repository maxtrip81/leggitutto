#!/bin/bash
# Compila LeggiTutto.app per macOS e crea l'immagine disco LeggiTutto.dmg.
# Serve Python 3.12 (da www.python.org oppure: brew install python@3.12).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3.12}
"$PY" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller packaging/LeggiTutto.spec --noconfirm
# Firma "ad hoc": necessaria sui Mac con processore Apple per avviare l'app.
codesign --force --deep --sign - dist/LeggiTutto.app
rm -f dist/LeggiTutto.dmg
mkdir -p dist/dmg && rm -rf dist/dmg/* && cp -R dist/LeggiTutto.app dist/dmg/ && ln -s /Applications dist/dmg/Applicazioni
hdiutil create -volname LeggiTutto -srcfolder dist/dmg -ov -format UDZO dist/LeggiTutto.dmg
echo "Pronto: dist/LeggiTutto.app e dist/LeggiTutto.dmg"
