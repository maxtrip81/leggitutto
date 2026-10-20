# LeggiTutto

*[Versione italiana](README.md)*

**Converts any file into a clean `.txt` text file, designed for people who read with speech or a braille display.**

Created by **Massimiliano Mascioli Trippa** — [max@maxtrip.it](mailto:max@maxtrip.it)

It works on Windows and macOS. It can be used entirely from the keyboard and works with NVDA, JAWS, Narrator and VoiceOver: it uses the system's native controls and announces progress through the screen reader.

## Language

The app starts in Italian. To switch to English: **Strumenti → Lingua / Language → English** menu, or **Opzioni → Generale → Lingua / Language**. Menus, windows, messages and the user guide change immediately, and the choice is remembered. The Windows installer is also available in Italian and English.

## What it does

- **Documents and books** (PDF, Word, LibreOffice, RTF, PowerPoint, Excel, ePub, MOBI, FB2, HTML, Markdown and more): extracts the text and removes everything that gets in the way of reading:
  - page numbers ("12", "- 12 -", "Page 12 of 300", Roman numerals);
  - headers and footers repeated on every page;
  - footnotes and note reference marks (¹, [3], asterisks);
  - words split by a hyphen at the end of a line and lines broken in the middle of a sentence;
  - table of contents dot leaders, decorative lines, invisible characters, web page menus and ads.

  Tables become sentences such as `Name: Anna; Role: Director.`, easy to listen to.
- **Images and scanned PDFs**: optical character recognition (OCR) with Tesseract, with the same cleanup.
- **Audio and video** (MP3, WAV, M4A, MP4, MOV, MKV, etc.): speech transcription with Whisper. If several people speak, each turn begins with `Speaker 1:`, `Speaker 2:`... Everything happens on your computer, without sending files over the Internet.
- **Protected files**: PDFs that only restrict copying or printing are converted directly; for PDFs and Office documents with an opening password you are asked for the password. Books with DRM (Adobe, Kindle, Apple) are **not** unlocked: the program says so and explains how to get an accessible copy legally.
- **ZIP archives** and **whole folders**: every file inside is converted.

The text is saved next to the original with the same name (`book.pdf` → `book.txt`), or in a folder of your choice. UTF-8 encoding (or ANSI for old braille devices), with optional line wrapping.

## How to use it

1. Start LeggiTutto.
2. Drag files into the window (or onto the app icon), or press **Ctrl+O** (**Cmd+O** on the Mac). On Windows you can also use **Send to → LeggiTutto** from the right-click menu of a file.
3. Conversion starts by itself. When it finishes, a window tells you how it went and offers to open the text.

| Key | Action |
|---|---|
| Ctrl+O | Add files |
| Ctrl+Shift+O | Add a folder |
| F5 | Convert |
| Ctrl+I | Stop |
| Delete | Remove the selected files from the list |
| Ctrl+L | Open the last text created |
| Ctrl+, | Options |
| F1 | User guide |

In the **Options** you can turn off each cleanup rule, choose the transcription quality, the spoken language, the number of people speaking (this makes speaker recognition more accurate) and whether to add the time of each turn.

## Download

Ready-made installers are on the [Releases page](https://github.com/maxtrip81/leggitutto/releases/latest):
- `LeggiTutto-Windows-Setup.exe` for Windows 10 and 11 (64-bit);
- `LeggiTutto-macOS-AppleSilicon.dmg` and `LeggiTutto-macOS-Intel.dmg` for macOS 11 or later.

The Mac app is not signed with an Apple certificate: the first time, open it with **Control-click → Open**, or from Terminal: `xattr -dr com.apple.quarantine /Applications/LeggiTutto.app`.

## Optional additional programs (free)

| Program | What it is for | How to install it |
|---|---|---|
| Tesseract OCR | images and scanned PDFs | Windows: github.com/UB-Mannheim/tesseract/wiki. Mac: `brew install tesseract tesseract-lang` |
| LibreOffice | old `.doc`, `.ppt` and rare formats | libreoffice.org (on Windows Microsoft Word works too) |
| Calibre | MOBI, AZW3, LIT and other e-books | calibre-ebook.com |

## Audio and video models

The first time they are used, they are downloaded and kept in the app's data folder (`%APPDATA%\LeggiTutto\modelli` on Windows, `~/Library/Application Support/LeggiTutto/modelli` on the Mac): the chosen Whisper model (from 75 MB to 3 GB) and two small models to tell speakers apart (about 33 MB). After that everything also works offline.

## Running from source

```
pip install -r requirements.txt
python LeggiTutto.py                                   # window
python LeggiTutto.py --cli --ui en book.pdf -o Texts   # command line, English messages
```

## Author

LeggiTutto was created by **Massimiliano Mascioli Trippa**. For reports, suggestions or problems write to [max@maxtrip.it](mailto:max@maxtrip.it).

© 2026 Massimiliano Mascioli Trippa
