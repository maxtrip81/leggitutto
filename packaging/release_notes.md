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
