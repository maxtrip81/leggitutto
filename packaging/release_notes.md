**Italiano** · [English below](#english)

LeggiTutto converte qualsiasi file (documenti, libri, pagine web, immagini, audio e video) in un file di testo .txt pulito e accessibile.

Creato da **Massimiliano Mascioli Trippa** — per segnalazioni e suggerimenti: [max@maxtrip.it](mailto:max@maxtrip.it)

## Quale file scaricare

- **Windows 10 e 11**: LeggiTutto-Windows-Setup.exe
- **Mac con processore Apple (M1, M2, M3, M4)**: LeggiTutto-macOS-AppleSilicon.dmg
- **Mac con processore Intel**: LeggiTutto-macOS-Intel.dmg

Per sapere che processore ha il tuo Mac: menu Apple, poi «Informazioni su questo Mac», alla voce «Chip» o «Processore».

## Installazione

**Windows**: avvia LeggiTutto-Windows-Setup.exe. Se compare l'avviso di Windows SmartScreen, scegli «Ulteriori informazioni» e poi «Esegui comunque» (il programma non è firmato digitalmente). Durante l'installazione puoi aggiungere LeggiTutto al menu «Invia a» del clic destro.

**Mac**: apri il file .dmg e trascina LeggiTutto nella cartella Applicazioni. La prima volta aprilo con Ctrl+clic (o VO+Maiuscole+M con VoiceOver) e scegli «Apri», perché l'app non è firmata da Apple.

## Primo utilizzo

Trascina un file nella finestra oppure premi Ctrl+O (Cmd+O sul Mac). Il testo viene salvato accanto all'originale. F1 apre la guida completa.

Per immagini e PDF scansionati serve Tesseract OCR; per i vecchi file .doc serve LibreOffice; per MOBI e AZW3 serve Calibre. Sono gratuiti: la guida spiega come installarli. Per audio e video, al primo utilizzo i modelli di riconoscimento vengono scaricati automaticamente.

## Verifica dei file

Il file SHA256SUMS.txt contiene le impronte digitali SHA-256 dei file di installazione: servono a controllare che il file scaricato sia integro e identico a quello pubblicato. Su Windows: `certutil -hashfile LeggiTutto-Windows-Setup.exe SHA256`; sul Mac: `shasum -a 256 LeggiTutto-macOS-AppleSilicon.dmg`.

---

<a id="english"></a>
## English

LeggiTutto converts any file (documents, books, web pages, images, audio and video) into a clean, accessible plain text (.txt) file. The app starts in Italian: to switch to English open the **Strumenti** (Tools) menu, submenu **Lingua / Language**, and choose **English**. The choice is remembered.

Created by **Massimiliano Mascioli Trippa** — for reports and suggestions: [max@maxtrip.it](mailto:max@maxtrip.it)

**Which file to download**
- **Windows 10 and 11**: LeggiTutto-Windows-Setup.exe (the installer lets you choose Italian or English)
- **Mac with Apple processor (M1, M2, M3, M4)**: LeggiTutto-macOS-AppleSilicon.dmg
- **Mac with Intel processor**: LeggiTutto-macOS-Intel.dmg

**Installation**
- **Windows**: run LeggiTutto-Windows-Setup.exe. If Windows SmartScreen appears, choose "More info" and then "Run anyway" (the program is not digitally signed). During installation you can add LeggiTutto to the "Send to" right-click menu.
- **Mac**: open the .dmg file and drag LeggiTutto into Applications. The first time, open it with Control-click (or VO+Shift+M with VoiceOver) and choose "Open", because the app is not signed by Apple.

**First use**: drag a file into the window or press Ctrl+O (Cmd+O on the Mac). The text is saved next to the original. F1 opens the full user guide.

The SHA256SUMS.txt file contains the SHA-256 fingerprints of the installers, to check that a downloaded file is intact and identical to the published one.
