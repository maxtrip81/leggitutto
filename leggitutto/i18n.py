"""Lingua dell'interfaccia: italiano (predefinito) o inglese.

I testi nel codice sono scritti in italiano e passano per ``_()``: se la lingua scelta
è l'inglese viene restituita la traduzione presente in ``EN``.
"""

from __future__ import annotations

_language = "it"


def set_language(code: str):
    global _language
    _language = code if code in ("it", "en") else "it"


def get_language() -> str:
    return _language


def _(text: str) -> str:
    if _language == "en":
        return EN.get(text, text)
    return text


def ngettext(n: int, singular: str, plural: str) -> str:
    if _language == "en" and n == 1 and singular in EN_ONE:
        return EN_ONE[singular]
    return _(singular if n == 1 else plural)


# In italiano "file" non cambia al plurale, in inglese sì.
EN_ONE = {
    "{n} file nell'elenco.": "{n} file in the list.",
    "Conversione avviata: {n} file.": "Conversion started: {n} file.",
}

EN = {
    # --- Finestra principale
    "Comando": "Command",
    "Control": "Control",
    "{app} - convertitore accessibile in testo": "{app} - accessible text converter",
    "Trascina qui i file da convertire in testo: documenti, libri, pagine web, immagini, audio o video. "
    "Oppure premi {mod}+O per sceglierli. F1 apre la guida.":
        "Drag here the files to convert to text: documents, books, web pages, images, audio or video. "
        "Or press {mod}+O to choose them. F1 opens the help.",
    "&File da convertire:": "&Files to convert:",
    "File da convertire": "Files to convert",
    "Elenco dei file da convertire. Canc toglie i file selezionati.":
        "List of files to convert. Delete removes the selected files.",
    "&Aggiungi file...": "&Add files...",
    "Aggiungi &cartella...": "Add fol&der...",
    "&Togli dall'elenco": "&Remove from list",
    "S&vuota l'elenco": "Cl&ear list",
    "Con&verti (F5)": "Con&vert (F5)",
    "Con&verti": "Con&vert",
    "&Interrompi": "&Stop",
    "&Opzioni...": "&Options...",
    "Apri l'&ultimo testo creato": "Open the &last text created",
    "Apri la cartella dell'ultimo testo": "Open the folder of the last text",
    "Avanzamento:": "Progress:",
    "Avanzamento": "Progress",
    "Pronto.": "Ready.",
    "Pronto": "Ready",
    "&Registro delle attività:": "Activity lo&g:",
    "Registro delle attività": "Activity log",
    "{app} {version} pronto. Trascina i file nella finestra o premi {mod}+O.":
        "{app} {version} ready. Drag files into the window or press {mod}+O.",
    # --- Menu
    "&File": "&File",
    "&Esci": "E&xit",
    "&Strumenti": "&Tools",
    "&Aiuto": "&Help",
    "&Guida": "&User guide",
    "&Programmi aggiuntivi": "&Additional programs",
    "&Scrivi all'autore": "&Write to the author",
    "&Informazioni su {app}": "&About {app}",
    # --- Elenco e conversione
    "File non trovato: {path}": "File not found: {path}",
    "{n} file aggiunto all'elenco.": "{n} file added to the list.",
    "{n} file aggiunti all'elenco.": "{n} files added to the list.",
    "Scegli i file da convertire": "Choose the files to convert",
    "Scegli una cartella: verranno convertiti tutti i file che contiene":
        "Choose a folder: all the files it contains will be converted",
    "{n} file nell'elenco.": "{n} files in the list.",
    "Elenco svuotato.": "List cleared.",
    "L'elenco è vuoto. Trascina dei file nella finestra o premi {mod}+O per sceglierli.":
        "The list is empty. Drag files into the window or press {mod}+O to choose them.",
    "Conversione avviata: {n} file.": "Conversion started: {n} files.",
    "Interruzione in corso...": "Stopping...",
    "Interruzione in corso.": "Stopping.",
    "Creato: {path}": "Created: {path}",
    "Conversione interrotta.": "Conversion stopped.",
    "Errore con {name}: {exc}": "Error with {name}: {exc}",
    "errore imprevisto: {exc}": "unexpected error: {exc}",
    "Errore imprevisto con {name}: {exc}": "Unexpected error with {name}: {exc}",
    "Il file «{name}» è protetto da password.\nScrivi la password e premi Invio.":
        "The file “{name}” is password protected.\nType the password and press Enter.",
    "La password per «{name}» non è corretta. Riprova.": "The password for “{name}” is not correct. Try again.",
    "Password richiesta": "Password required",
    "File {n} di {total}: {name}": "File {n} of {total}: {name}",
    "Conversione di {name}": "Converting {name}",
    "{n} per cento": "{n} percent",
    "{n} file convertito.": "{n} file converted.",
    "{n} file convertiti.": "{n} files converted.",
    "{n} file non convertito:": "{n} file not converted:",
    "{n} file non convertiti:": "{n} files not converted:",
    "Il testo è stato salvato in: {path}": "The text was saved in: {path}",
    "I testi sono stati salvati in: {path}": "The texts were saved in: {path}",
    "Nessun file convertito.": "No files converted.",
    "Vuoi aprirlo adesso?": "Do you want to open it now?",
    "Vuoi aprire la cartella adesso?": "Do you want to open the folder now?",
    "Conversione terminata": "Conversion finished",
    "&Apri il testo": "&Open the text",
    "&Apri la cartella": "&Open the folder",
    "&Chiudi": "&Close",
    "Impossibile aprire {target}: {exc}": "Unable to open {target}: {exc}",
    "È in corso una conversione. Vuoi interromperla e uscire?":
        "A conversion is in progress. Do you want to stop it and exit?",
    "Attendi la fine della conversione per cambiare le opzioni.":
        "Wait for the conversion to finish before changing the options.",
    "Opzioni salvate.": "Options saved.",
    "Lingua cambiata: italiano.": "Language changed: Italian.",
    "Lingua cambiata: inglese.": "Language changed: English.",
    # --- Guida, programmi aggiuntivi, informazioni
    "Guida di {app}": "{app} user guide",
    "Programmi aggiuntivi": "Additional programs",
    "Tesseract OCR: installato ({path}). Lingue usate: {langs}.":
        "Tesseract OCR: installed ({path}). Languages used: {langs}.",
    "Attenzione: manca la lingua italiana di Tesseract (ita).":
        "Warning: the Italian language for Tesseract (ita) is missing.",
    "Tesseract OCR: non installato. Serve per immagini e PDF scansionati.":
        "Tesseract OCR: not installed. It is needed for images and scanned PDFs.",
    "vecchi file .doc, .ppt e formati rari": "old .doc and .ppt files and rare formats",
    "eBook MOBI, AZW3, LIT e simili": "MOBI, AZW3, LIT and similar e-books",
    "file DjVu": "DjVu files",
    "installato ({path}).": "installed ({path}).",
    "non installato. Serve per {use}.": "not installed. It is needed for {use}.",
    "I modelli per audio e video vengono scaricati automaticamente al primo utilizzo.":
        "The audio and video models are downloaded automatically the first time they are used.",
    "Informazioni su {app}": "About {app}",
    "Converte qualsiasi file in testo semplice accessibile, per la lettura con sintesi vocale e display braille.":
        "Converts any file into accessible plain text, for reading with speech and braille displays.",
    "Creato da {author}": "Created by {author}",
    "Posta elettronica: {email}": "Email: {email}",
    "Usa software libero: PyMuPDF, Tesseract, faster-whisper (modelli Whisper di OpenAI), "
    "sherpa-onnx con i modelli pyannote e WeSpeaker, wxPython.":
        "Uses free software: PyMuPDF, Tesseract, faster-whisper (OpenAI Whisper models), "
        "sherpa-onnx with the pyannote and WeSpeaker models, wxPython.",
    # --- Opzioni
    "Opzioni": "Options",
    "Schede delle opzioni": "Option tabs",
    "Generale": "General",
    "Documenti": "Documents",
    "Audio e video": "Audio and video",
    "Salvataggio": "Saving",
    "Annulla": "Cancel",
    "Converti &subito i file trascinati o aggiunti": "Convert dropped or added files &immediately",
    "&Apri il file di testo al termine della conversione": "&Open the text file when the conversion ends",
    "Togli i &numeri di pagina": "Remove page &numbers",
    "Togli &intestazioni e piè di pagina ripetuti": "Remove repeated &headers and footers",
    "Togli le &note a piè di pagina": "Remove &footnotes",
    "Togli i &richiami di nota nel testo (numerini, asterischi)":
        "Remove note &reference marks in the text (small numbers, asterisks)",
    "Ricomponi i &paragrafi spezzati a fine riga": "Rejoin &paragraphs broken at line ends",
    "Togli &elementi superflui (puntini degli indici, righe decorative, menu delle pagine web)":
        "Remove &unnecessary elements (table of contents dot leaders, decorative lines, web page menus)",
    "Includi le note del &relatore delle presentazioni": "Include presentation &speaker notes",
    "Leggi il testo di &immagini e pagine scansionate (OCR)": "Read text from &images and scanned pages (OCR)",
    "&Lingue per l'OCR (codici Tesseract separati da +):": "OCR &languages (Tesseract codes separated by +):",
    "Per esempio ita+eng per italiano e inglese": "For example ita+eng for Italian and English",
    "&Qualità della trascrizione:": "Transcription &quality:",
    "&Lingua parlata:": "&Spoken language:",
    "Indica &chi sta parlando (Persona 1, Persona 2...)": "Show &who is speaking (Speaker 1, Speaker 2...)",
    "Aggiungi l'&orario di ogni intervento": "Add the &time of each turn",
    "Usa la scheda &video NVIDIA, se presente (più veloce)": "Use the NVIDIA &graphics card, if present (faster)",
    "&Numero di persone che parlano (0 = riconoscimento automatico):":
        "&Number of people speaking (0 = automatic recognition):",
    "Salva il testo nella &stessa cartella del file originale": "Save the text in the &same folder as the original file",
    "Cartella di &destinazione:": "&Destination folder:",
    "&Scegli la cartella di destinazione...": "&Choose the destination folder...",
    "Scegli la cartella in cui salvare i file di testo": "Choose the folder where the text files will be saved",
    "&Codifica del testo:": "&Text encoding:",
    "&Vai a capo ogni tanti caratteri (0 = mai, consigliato):":
        "&Wrap lines every N characters (0 = never, recommended):",
    # Voci degli elenchi in settings.py
    "Minimo: velocissimo, qualità bassa (75 MB)": "Minimum: very fast, low quality (75 MB)",
    "Base: veloce, qualità discreta (150 MB)": "Basic: fast, fair quality (150 MB)",
    "Medio: buon equilibrio (consigliato, 500 MB)": "Medium: good balance (recommended, 500 MB)",
    "Grande: qualità alta, lento (1,5 GB)": "Large: high quality, slow (1.5 GB)",
    "Turbo: qualità molto alta, veloce sui computer recenti (1,6 GB)":
        "Turbo: very high quality, fast on recent computers (1.6 GB)",
    "Massimo: qualità migliore, molto lento (3 GB)": "Maximum: best quality, very slow (3 GB)",
    "Riconoscimento automatico": "Automatic recognition",
    "Italiano": "Italian",
    "Inglese": "English",
    "Francese": "French",
    "Tedesco": "German",
    "Spagnolo": "Spanish",
    "Portoghese": "Portuguese",
    "Olandese": "Dutch",
    "Rumeno": "Romanian",
    "Polacco": "Polish",
    "Russo": "Russian",
    "Ucraino": "Ukrainian",
    "Arabo": "Arabic",
    "Cinese": "Chinese",
    "Giapponese": "Japanese",
    "UTF-8 (consigliata)": "UTF-8 (recommended)",
    "UTF-8 con BOM (per vecchi programmi Windows)": "UTF-8 with BOM (for old Windows programs)",
    "ANSI Windows-1252 (per vecchi dispositivi braille)": "ANSI Windows-1252 (for old braille devices)",
    # --- Riga di comando
    "Converte file di ogni tipo in testo .txt accessibile.": "Converts files of any kind into accessible .txt text.",
    "file o cartelle da convertire": "files or folders to convert",
    "cartella di destinazione (predefinita: accanto all'originale)":
        "destination folder (default: next to the original)",
    "password per i documenti protetti": "password for protected documents",
    "modello di riconoscimento vocale": "speech recognition model",
    "lingua dell'audio, es. it, en (predefinita: automatica)": "audio language, e.g. it, en (default: automatic)",
    "numero di persone che parlano (0 = automatico)": "number of people speaking (0 = automatic)",
    "non distinguere le voci": "do not tell speakers apart",
    "aggiungi l'orario a ogni intervento": "add the time to each turn",
    "non togliere numeri di pagina, note, intestazioni": "do not remove page numbers, notes, headers",
    "va a capo ogni N caratteri (0 = mai)": "wrap lines every N characters (0 = never)",
    "lingua dei messaggi (it, en)": "language of messages (it, en)",
    "Password per {name}: ": "Password for {name}: ",
    "creato {path}": "created {path}",
    "errore: {exc}": "error: {exc}",
    # --- Messaggi del motore di conversione
    "Attenzione: {message}": "Warning: {message}",
    "documento Office non riconosciuto.": "Office document not recognized.",
    "il file non esiste o non è leggibile.": "the file does not exist or cannot be read.",
    "il file è vuoto.": "the file is empty.",
    "nel file non è stato trovato testo da salvare.": "no text to save was found in the file.",
    "testo": "text",
    "formato del file non riconosciuto ({ext}).": "file format not recognized ({ext}).",
    "senza estensione": "no extension",
    "Archivio: conversione di {name}": "Archive: converting {name}",
    "l'archivio è protetto da password: {exc}": "the archive is password protected: {exc}",
    "File: {name}": "File: {name}",
    "il documento è protetto da password e non è stata inserita la password.":
        "the document is password protected and no password was entered.",
    "la password inserita non è corretta.": "the password entered is not correct.",
    "documento Word non leggibile: {exc}": "unreadable Word document: {exc}",
    "il documento OpenDocument è cifrato con password: aprilo con LibreOffice e salvalo senza password, poi riprova.":
        "the OpenDocument file is encrypted with a password: open it with LibreOffice, "
        "save it without a password, then try again.",
    "documento OpenDocument non leggibile: {exc}": "unreadable OpenDocument file: {exc}",
    "presentazione non leggibile: {exc}": "unreadable presentation: {exc}",
    "foglio di calcolo non leggibile: {exc}": "unreadable spreadsheet: {exc}",
    "per i file {ext} serve LibreOffice (gratuito, www.libreoffice.org) oppure Microsoft Word installato sul computer.":
        "{ext} files need LibreOffice (free, www.libreoffice.org) or Microsoft Word installed on the computer.",
    "LibreOffice non è riuscito a convertire il file: {exc}": "LibreOffice could not convert the file: {exc}",
    "Foglio: {name}": "Sheet: {name}",
    "Diapositiva {n}": "Slide {n}",
    "Diapositiva {n} di {total}": "Slide {n} of {total}",
    "Note del relatore:": "Speaker notes:",
    "Note": "Notes",
    "Colonna {n}": "Column {n}",
    "Analisi dell'impaginazione": "Analysing the page layout",
    "il file non si apre (forse è danneggiato): {exc}": "the file cannot be opened (it may be damaged): {exc}",
    "il documento non contiene pagine.": "the document has no pages.",
    "Pagina {n} di {total}": "Page {n} of {total}",
    "OCR non riuscito a pagina {n}: {exc}": "OCR failed on page {n}: {exc}",
    "il documento contiene immagini o pagine scansionate: per leggerle installa Tesseract OCR (vedi la Guida, tasto F1).":
        "the document contains images or scanned pages: to read them install Tesseract OCR (see the user guide, F1 key).",
    "nel documento non è stato trovato testo leggibile.": "no readable text was found in the document.",
    "il file è un'immagine: per leggerne il testo installa Tesseract OCR (vedi la Guida, tasto F1).":
        "the file is an image: to read its text install Tesseract OCR (see the user guide, F1 key).",
    "immagine non leggibile: {exc}": "unreadable image: {exc}",
    "Riconoscimento del testo, immagine {n} di {total}": "Recognizing text, image {n} of {total}",
    "Immagine: {alt}": "Image: {alt}",
    "l'archivio web non contiene una pagina leggibile.": "the web archive does not contain a readable page.",
    "ePub non valido: {exc}": "invalid ePub: {exc}",
    "Capitolo {n} di {total}": "Chapter {n} of {total}",
    "l'archivio non contiene un libro FB2.": "the archive does not contain an FB2 book.",
    "Calibre non è riuscito a convertire il file: {exc}": "Calibre could not convert the file: {exc}",
    "per i file {ext} serve Calibre (gratuito, calibre-ebook.com): installalo e riprova.":
        "{ext} files need Calibre (free, calibre-ebook.com): install it and try again.",
    "il libro è protetto da DRM (blocco anticopia dell'editore). LeggiTutto non rimuove i DRM: "
    "puoi chiedere una copia accessibile all'editore, alla tua biblioteca o ai servizi per persone "
    "con disabilità visiva (in Italia ad esempio la Biblioteca Italiana per i Ciechi o il Libro Parlato), "
    "che possono fornirla grazie al Trattato di Marrakech.":
        "the book is protected by DRM (the publisher's copy protection). LeggiTutto does not remove DRM: "
        "you can ask the publisher, your library or services for people with visual impairments for an "
        "accessible copy; under the Marrakesh Treaty they are allowed to provide one.",
    "Tesseract non è installato": "Tesseract is not installed",
    # --- Audio e video
    "Caricamento del modello di riconoscimento vocale «{name}». "
    "Al primo utilizzo viene scaricato da Internet: può richiedere alcuni minuti.":
        "Loading the speech recognition model “{name}”. "
        "The first time it is downloaded from the Internet: this may take a few minutes.",
    "Preparazione del riconoscimento vocale": "Preparing speech recognition",
    "scheda video non utilizzabile ({exc}), uso il processore.": "graphics card not usable ({exc}), using the processor.",
    "impossibile caricare il modello vocale «{name}». Controlla la connessione a Internet "
    "(serve solo la prima volta). Dettagli: {exc}":
        "unable to load the speech model “{name}”. Check your Internet connection "
        "(it is only needed the first time). Details: {exc}",
    "il file audio o video non si apre ({exc}).": "the audio or video file cannot be opened ({exc}).",
    "il file non contiene una traccia audio.": "the file does not contain an audio track.",
    "Estrazione dell'audio": "Extracting the audio",
    "Estrazione dell'audio: {percent}%": "Extracting the audio: {percent}%",
    "traccia audio non leggibile ({exc}).": "unreadable audio track ({exc}).",
    "la parte finale del file è danneggiata: trascritto solo l'inizio.":
        "the end of the file is damaged: only the beginning was transcribed.",
    "la traccia audio è vuota.": "the audio track is empty.",
    "Durata: {duration}.": "Duration: {duration}.",
    "Lingua riconosciuta: {language}.": "Language recognized: {language}.",
    "Trascrizione: {done} di {total}": "Transcribing: {done} of {total}",
    "Nel file «{name}» non è stato riconosciuto parlato.": "No speech was recognized in the file “{name}”.",
    "non è stato possibile distinguere le voci ({exc}); trascrizione senza nomi.":
        "it was not possible to tell the voices apart ({exc}); transcript without names.",
    "Trascrizione di «{name}»": "Transcript of “{name}”",
    "Durata: {duration}. Lingua: {language}.": "Duration: {duration}. Language: {language}.",
    "Voci diverse riconosciute: {n}.": "Different voices recognized: {n}.",
    "Persona {n}": "Speaker {n}",
    "Trascrizione completata": "Transcription completed",
    "{n} ora": "{n} hour",
    "{n} ore": "{n} hours",
    "{n} minuto": "{n} minute",
    "{n} minuti": "{n} minutes",
    "{n} secondo": "{n} second",
    "{n} secondi": "{n} seconds",
    "e": "and",
    "Scaricamento di {label} (solo la prima volta)...": "Downloading the {label} (only the first time)...",
    "Scaricamento di {label}: {percent}%": "Downloading the {label}: {percent}%",
    "modello di segmentazione delle voci": "voice segmentation model",
    "modello di riconoscimento delle voci": "speaker recognition model",
    "configurazione dei modelli delle voci non valida": "invalid speaker model configuration",
    "Riconoscimento delle voci": "Recognizing the speakers",
}
