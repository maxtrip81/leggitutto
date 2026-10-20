# LeggiTutto

**Converte qualsiasi file in un file di testo `.txt` pulito, pensato per chi legge con la sintesi vocale o con il display braille.**

Creato da **Massimiliano Mascioli Trippa** — [max@maxtrip.it](mailto:max@maxtrip.it)

Funziona su Windows e macOS. Si usa interamente da tastiera ed è compatibile con NVDA, JAWS, Assistente vocale e VoiceOver: usa i controlli nativi del sistema e annuncia l'avanzamento attraverso il lettore di schermo.

## Cosa fa

- **Documenti e libri** (PDF, Word, LibreOffice, RTF, PowerPoint, Excel, ePub, MOBI, FB2, HTML, Markdown e altri): estrae il testo e toglie tutto ciò che disturba la lettura:
  - numeri di pagina ("12", "- 12 -", "Pagina 12 di 300", numeri romani);
  - intestazioni e piè di pagina ripetuti su ogni pagina;
  - note a piè di pagina e richiami di nota (¹, [3], asterischi);
  - parole spezzate dal trattino a fine riga e righe interrotte a metà frase;
  - puntini degli indici, righe decorative, caratteri invisibili, menu e pubblicità delle pagine web.

  Le tabelle diventano frasi del tipo `Nome: Anna; Ruolo: Direttrice.`, facili da ascoltare.
- **Immagini e PDF scansionati**: riconoscimento ottico del testo (OCR) con Tesseract, con la stessa pulizia.
- **Audio e video** (MP3, WAV, M4A, MP4, MOV, MKV, ecc.): trascrizione del parlato con Whisper. Se parlano più persone, ogni intervento comincia con `Persona 1:`, `Persona 2:`... Tutto avviene sul computer, senza inviare file su Internet.
- **File protetti**: i PDF con restrizioni di copia/stampa si convertono direttamente; per PDF e documenti Office con password di apertura viene chiesta la password. I libri con DRM (Adobe, Kindle, Apple) **non** vengono sbloccati: il programma lo segnala e indica come ottenere una copia accessibile in modo legale (editore, biblioteca, servizi previsti dal Trattato di Marrakech).
- **Archivi ZIP** e **cartelle intere**: converte tutti i file contenuti.

Il testo viene salvato accanto all'originale con lo stesso nome (`libro.pdf` → `libro.txt`), oppure in una cartella a scelta. Codifica UTF-8 (o ANSI per vecchi dispositivi braille), con a capo automatico facoltativo.

## Come si usa

1. Avvia LeggiTutto.
2. Trascina i file nella finestra (o sull'icona dell'app), oppure premi **Ctrl+O** (sul Mac **Cmd+O**). Su Windows puoi anche usare il menu **Invia a → LeggiTutto** dal clic destro su un file.
3. La conversione parte da sola. Al termine una finestra ti dice com'è andata e propone di aprire il testo.

| Tasto | Azione |
|---|---|
| Ctrl+O | Aggiungi file |
| Ctrl+Maiusc+O | Aggiungi una cartella |
| F5 | Converti |
| Ctrl+I | Interrompi |
| Canc | Togli i file selezionati dall'elenco |
| Ctrl+L | Apri l'ultimo testo creato |
| Ctrl+, | Opzioni |
| F1 | Guida |

Nelle **Opzioni** puoi disattivare ogni regola di pulizia, scegliere la qualità della trascrizione, la lingua parlata, il numero di persone che parlano (rende più preciso il riconoscimento delle voci) e l'aggiunta dell'orario a ogni intervento.

## Installazione

### Pacchetti pronti
Il flusso GitHub Actions in `.github/workflows/build.yml` compila automaticamente:
- `LeggiTutto-Setup.exe` per Windows 10 e 11 (64 bit);
- `LeggiTutto-macOS-AppleSilicon.dmg` e `LeggiTutto-macOS-Intel.dmg` per macOS 11 o successivo.

Basta caricare il progetto su GitHub e avviare il flusso "Compila LeggiTutto" dalla scheda Actions (oppure creare un tag `v1.0.0`): i file si scaricano dagli "Artifacts".

Finché non viene attivata la firma digitale (vedi [FIRMA_DIGITALE.md](FIRMA_DIGITALE.md)) Windows e macOS mostrano un avviso al primo avvio. L'app per Mac non è firmata con un certificato Apple: la prima volta aprila con **Ctrl+clic → Apri**, oppure da Terminale: `xattr -dr com.apple.quarantine /Applications/LeggiTutto.app`.

### Compilare da sé
- **Windows**: installa Python 3.12 da python.org, poi fai doppio clic su `packaging\build_windows.bat`. Se è installato Inno Setup crea anche l'installazione.
- **macOS**: installa Python 3.12, poi da Terminale `./packaging/build_macos.sh`.

### Avviare dal codice sorgente
```
pip install -r requirements.txt
python LeggiTutto.py                              # finestra
python LeggiTutto.py --cli libro.pdf intervista.mp3 -o Testi   # riga di comando
python LeggiTutto.py --cli --help
```

## Programmi aggiuntivi facoltativi (gratuiti)

| Programma | A cosa serve | Come installarlo |
|---|---|---|
| Tesseract OCR | immagini e PDF scansionati | Windows: github.com/UB-Mannheim/tesseract/wiki (seleziona la lingua italiana). Mac: `brew install tesseract tesseract-lang` |
| LibreOffice | vecchi `.doc`, `.ppt`, formati rari | libreoffice.org (su Windows va bene anche Microsoft Word) |
| Calibre | MOBI, AZW3, LIT e altri eBook | calibre-ebook.com |

Su Windows Tesseract si può includere direttamente nel programma: copia la cartella `C:\Program Files\Tesseract-OCR` in `packaging\tesseract` prima di compilare. Dal menu **Aiuto → Programmi aggiuntivi** si vede cosa è installato.

## Modelli per audio e video

Al primo utilizzo vengono scaricati e conservati nella cartella dei dati dell'app (`%APPDATA%\LeggiTutto\modelli` su Windows, `~/Library/Application Support/LeggiTutto/modelli` sul Mac):
- il modello Whisper scelto (da 75 MB per "Minimo" a 3 GB per "Massimo"; consigliati "Medio" o, sui computer recenti, "Turbo");
- due piccoli modelli per distinguere le voci (circa 33 MB: segmentazione pyannote e riconoscimento WeSpeaker, tramite sherpa-onnx).

Dopo il primo scaricamento tutto funziona anche senza Internet.

## Struttura del progetto

```
LeggiTutto.py              avvio
leggitutto/app.py          finestra accessibile (wxPython)
leggitutto/converter.py    riconoscimento del formato e salvataggio
leggitutto/cleaner.py      pulizia del testo (pagine, note, intestazioni, sillabazione)
leggitutto/extract_pdf.py  PDF, XPS, immagini; analisi dell'impaginazione
leggitutto/extract_office.py  Word, OpenDocument, RTF, PowerPoint, fogli di calcolo
leggitutto/extract_web.py  HTML, ePub, FB2, MOBI, Markdown, sottotitoli, testo
leggitutto/media.py        trascrizione audio/video (faster-whisper)
leggitutto/diarization.py  riconoscimento di chi parla (sherpa-onnx)
leggitutto/ocr.py          OCR (Tesseract)
tests/                     prove automatiche (python -m pytest tests)
packaging/                 ricetta PyInstaller, script di compilazione, installazione Windows
```

## Autore

LeggiTutto è stato creato da **Massimiliano Mascioli Trippa**. Per segnalazioni, suggerimenti o problemi scrivi a [max@maxtrip.it](mailto:max@maxtrip.it).

© 2026 Massimiliano Mascioli Trippa
