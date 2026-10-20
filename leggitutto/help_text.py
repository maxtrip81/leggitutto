"""Testo della Guida mostrata con F1."""

from . import APP_NAME, AUTHOR, AUTHOR_EMAIL, COPYRIGHT, __version__

GUIDE = f"""{APP_NAME} {__version__} - Guida

Creato da {AUTHOR} ({AUTHOR_EMAIL}).

{APP_NAME} trasforma qualsiasi file in un file di testo semplice (.txt), pulito e comodo da leggere con la sintesi vocale o con il display braille.

COME SI USA
1. Trascina uno o più file nella finestra. In alternativa premi Control+O (Comando+O sul Mac) per sceglierli, oppure Control+Maiuscole+O per aggiungere una cartella intera. Sul Mac puoi anche trascinare i file sull'icona dell'app nel Dock; su Windows sull'icona del programma.
2. La conversione parte da sola (puoi disattivarlo nelle Opzioni). Altrimenti premi F5 o il pulsante Converti.
3. Il file di testo viene salvato accanto all'originale, con lo stesso nome ed estensione .txt. Nelle Opzioni puoi scegliere un'altra cartella.
Al termine una finestra ti dice com'è andata e ti permette di aprire subito il testo.

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
Control+Virgola: opzioni (sul Mac Comando+Virgola)
F1: questa guida
Sul Mac usa il tasto Comando al posto di Control.

AUTORE
{APP_NAME} è stato creato da {AUTHOR}. Per segnalazioni, suggerimenti o problemi scrivi a {AUTHOR_EMAIL}, anche dal menu Aiuto, voce "Scrivi all'autore".
{COPYRIGHT}
"""
