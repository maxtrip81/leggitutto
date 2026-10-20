"""Testo della Guida mostrata con F1, in italiano e in inglese."""

from . import APP_NAME, AUTHOR, AUTHOR_EMAIL, COPYRIGHT, __version__
from .i18n import get_language

GUIDE_IT = f"""{APP_NAME} {__version__} - Guida

Creato da {AUTHOR} ({AUTHOR_EMAIL}).

{APP_NAME} trasforma qualsiasi file in un file di testo semplice (.txt), pulito e comodo da leggere con la sintesi vocale o con il display braille.

COME SI USA
1. Trascina uno o più file nella finestra. In alternativa premi Control+O (Comando+O sul Mac) per sceglierli, oppure Control+Maiuscole+O per aggiungere una cartella intera. Sul Mac puoi anche trascinare i file sull'icona dell'app nel Dock; su Windows sull'icona del programma o usare il menu "Invia a" del clic destro.
2. La conversione parte da sola (puoi disattivarlo nelle Opzioni). Altrimenti premi F5 o il pulsante Converti.
3. Il file di testo viene salvato accanto all'originale, con lo stesso nome ed estensione .txt. Nelle Opzioni puoi scegliere un'altra cartella.
Al termine una finestra ti dice com'è andata e ti permette di aprire subito il testo.

LINGUA
L'app è in italiano. Per passare all'inglese apri il menu Strumenti, sottomenu "Lingua / Language", e scegli English; oppure apri le Opzioni (Control+Virgola), scheda Generale, campo "Lingua / Language". La finestra si aggiorna subito e la scelta viene ricordata. Anche le scritte inserite nei testi convertiti (per esempio "Persona 1" nelle trascrizioni) seguono la lingua scelta.

COSA VIENE TOLTO DAI DOCUMENTI
- numeri di pagina, anche nella forma "Pagina 3 di 120" o "- 3 -";
- intestazioni e piè di pagina che si ripetono (titolo del libro, nome dell'editore...);
- note a piè di pagina e richiami di nota nel testo (i numerini o gli asterischi);
- parole spezzate dal trattino a fine riga e righe interrotte a metà frase;
- puntini degli indici, righe decorative, caratteri invisibili.
Le tabelle vengono lette riga per riga nella forma "Intestazione: valore", molto più chiara all'ascolto.
Ogni regola si può disattivare nelle Opzioni, scheda Documenti.

FORMATI SUPPORTATI
Documenti: PDF, Word (doc, docx), OpenOffice e LibreOffice (odt, ods, odp), RTF, PowerPoint (ppt, pptx), Excel (xls, xlsx), CSV, XPS, testo semplice in qualsiasi codifica.
Libri elettronici: ePub, MOBI e AZW senza DRM, FB2, DjVu, CHM, fumetti CBZ.
Web: pagine HTML e MHT (viene tenuto solo il contenuto principale, senza menu e pubblicità), Markdown.
Immagini e scansioni: JPG, PNG, TIFF anche multipagina, BMP, GIF, WebP, PDF scansionati (serve Tesseract, vedi sotto).
Sottotitoli: SRT, VTT, ASS.
Audio e video: MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, WMA, MP4, MOV, AVI, MKV, WEBM, WMV e quasi tutti gli altri.
Archivi ZIP: vengono convertiti tutti i file contenuti.

AUDIO E VIDEO
Il parlato viene trascritto direttamente sul computer: nessun file viene inviato su Internet. Al primo utilizzo vengono scaricati i modelli di riconoscimento (da 75 MB a 3 GB secondo la qualità scelta), poi funziona anche senza connessione.
Se parlano più persone, ogni intervento comincia con "Persona 1:", "Persona 2:" e così via. Se sai quante persone parlano, indicalo nelle Opzioni: il riconoscimento delle voci sarà più preciso.
La trascrizione richiede tempo: con la qualità "Medio" su un computer recente circa metà della durata dell'audio. La qualità "Turbo" è molto più precisa ed è consigliata sui computer recenti.

FILE PROTETTI
- PDF con password di apertura: viene chiesta la password. I PDF che vietano solo la copia o la stampa si convertono senza chiedere nulla.
- Word, Excel e PowerPoint con password: viene chiesta la password.
- Libri con DRM (Adobe, Kindle, Apple): {APP_NAME} non rimuove i DRM. Puoi chiederne una copia accessibile all'editore, alla tua biblioteca o ai servizi per persone con disabilità visiva (per esempio la Biblioteca Italiana per i Ciechi "Regina Margherita" o il Libro Parlato), che possono fornirla grazie al Trattato di Marrakech.

PROGRAMMI AGGIUNTIVI (FACOLTATIVI, GRATUITI)
- Tesseract OCR: serve per leggere immagini e PDF scansionati. Windows: installalo da github.com/UB-Mannheim/tesseract/wiki scegliendo anche la lingua italiana. Mac: da Terminale, brew install tesseract tesseract-lang.
- LibreOffice (www.libreoffice.org): serve per i vecchi formati .doc e .ppt e per altri formati rari. Su Windows, al suo posto va bene anche Microsoft Word.
- Calibre (calibre-ebook.com): serve per MOBI, AZW3, LIT e altri formati di eBook.
Dal menu Aiuto, voce "Programmi aggiuntivi", puoi controllare quali sono già installati.

TASTI RAPIDI
Control+O: aggiungi file
Control+Maiuscole+O: aggiungi una cartella
F5: converti
Control+I: interrompi la conversione
Canc: togli dall'elenco i file selezionati
Control+L: apri l'ultimo testo creato
Control+Maiuscole+L: apri la cartella dell'ultimo testo
Control+Virgola: opzioni (sul Mac Comando+Virgola)
F1: questa guida
Sul Mac usa il tasto Comando al posto di Control.

AUTORE
{APP_NAME} è stato creato da {AUTHOR}. Per segnalazioni, suggerimenti o problemi scrivi a {AUTHOR_EMAIL}, anche dal menu Aiuto, voce "Scrivi all'autore".
{COPYRIGHT}
"""

GUIDE_EN = f"""{APP_NAME} {__version__} - Help

Created by {AUTHOR} ({AUTHOR_EMAIL}).

{APP_NAME} turns any file into a plain text file (.txt), clean and comfortable to read with speech or a braille display.

HOW TO USE IT
1. Drag one or more files into the window. Or press Control+O (Command+O on the Mac) to choose them, or Control+Shift+O to add a whole folder. On the Mac you can also drop files on the app icon in the Dock; on Windows on the program icon, or use the "Send to" menu when you right-click a file.
2. Conversion starts by itself (you can turn this off in the Options). Otherwise press F5 or the Convert button.
3. The text file is saved next to the original, with the same name and the .txt extension. In the Options you can choose another folder.
When it is finished, a window tells you how it went and lets you open the text right away.

LANGUAGE
The app starts in Italian. To switch language open the Tools menu, submenu "Lingua / Language", and choose Italiano or English; or open the Options (Control+Comma), General tab, field "Lingua / Language". The window updates immediately and the choice is remembered. The labels added to converted texts (for example "Speaker 1" in transcripts) follow the chosen language too.

WHAT IS REMOVED FROM DOCUMENTS
- page numbers, also written as "Page 3 of 120" or "- 3 -";
- repeated headers and footers (book title, publisher name...);
- footnotes and note reference marks in the text (small numbers or asterisks);
- words split by a hyphen at the end of a line and lines broken in the middle of a sentence;
- dot leaders in tables of contents, decorative lines, invisible characters.
Tables are read row by row as "Header: value", which is much clearer to listen to.
Each rule can be turned off in the Options, Documents tab.

SUPPORTED FORMATS
Documents: PDF, Word (doc, docx), OpenOffice and LibreOffice (odt, ods, odp), RTF, PowerPoint (ppt, pptx), Excel (xls, xlsx), CSV, XPS, plain text in any encoding.
E-books: ePub, MOBI and AZW without DRM, FB2, DjVu, CHM, CBZ comics.
Web: HTML and MHT pages (only the main content is kept, without menus and ads), Markdown.
Images and scans: JPG, PNG, TIFF including multi-page, BMP, GIF, WebP, scanned PDFs (Tesseract is needed, see below).
Subtitles: SRT, VTT, ASS.
Audio and video: MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, WMA, MP4, MOV, AVI, MKV, WEBM, WMV and almost all others.
ZIP archives: every file inside is converted.

AUDIO AND VIDEO
Speech is transcribed directly on your computer: no file is sent over the Internet. The first time, the recognition models are downloaded (from 75 MB to 3 GB depending on the chosen quality); after that it also works offline.
If several people speak, each turn begins with "Speaker 1:", "Speaker 2:" and so on. If you know how many people are speaking, set it in the Options: speaker recognition will be more accurate.
Transcription takes time: with "Medium" quality on a recent computer, about half the length of the audio. "Turbo" quality is much more accurate and is recommended on recent computers.

PROTECTED FILES
- PDFs with an opening password: you are asked for the password. PDFs that only forbid copying or printing are converted without asking anything.
- Word, Excel and PowerPoint files with a password: you are asked for the password.
- Books with DRM (Adobe, Kindle, Apple): {APP_NAME} does not remove DRM. You can ask the publisher, your library or services for people with visual impairments for an accessible copy; under the Marrakesh Treaty they are allowed to provide one.

ADDITIONAL PROGRAMS (OPTIONAL, FREE)
- Tesseract OCR: needed to read images and scanned PDFs. Windows: install it from github.com/UB-Mannheim/tesseract/wiki and select the languages you need. Mac: in Terminal, brew install tesseract tesseract-lang.
- LibreOffice (www.libreoffice.org): needed for old .doc and .ppt files and other rare formats. On Windows, Microsoft Word works as well.
- Calibre (calibre-ebook.com): needed for MOBI, AZW3, LIT and other e-book formats.
In the Help menu, item "Additional programs", you can check which ones are already installed.
Tip: for English documents and audio you can set the OCR languages to eng in the Options (Documents tab) and the spoken language to English (Audio and video tab), or leave automatic recognition on.

KEYBOARD SHORTCUTS
Control+O: add files
Control+Shift+O: add a folder
F5: convert
Control+I: stop the conversion
Delete: remove the selected files from the list
Control+L: open the last text created
Control+Shift+L: open the folder of the last text
Control+Comma: options (Command+Comma on the Mac)
F1: this help
On the Mac use the Command key instead of Control.

AUTHOR
{APP_NAME} was created by {AUTHOR}. For reports, suggestions or problems write to {AUTHOR_EMAIL}, also from the Help menu, item "Write to the author".
{COPYRIGHT}
"""


def guide() -> str:
    return GUIDE_EN if get_language() == "en" else GUIDE_IT
