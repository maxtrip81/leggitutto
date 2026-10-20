@echo off
rem Compila LeggiTutto per Windows. Serve Python 3.12 da www.python.org.
rem Facoltativo: copia la cartella di Tesseract-OCR in packaging\tesseract per includerlo nel programma.
setlocal
cd /d "%~dp0\.."
py -3.12 -m venv .venv || goto :errore
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller || goto :errore
pyinstaller packaging\LeggiTutto.spec --noconfirm || goto :errore
echo.
echo Programma pronto in dist\LeggiTutto\LeggiTutto.exe
where iscc >nul 2>nul && iscc packaging\installer.iss && echo Installazione pronta in dist\LeggiTutto-Setup.exe
goto :eof
:errore
echo Compilazione non riuscita.
exit /b 1
