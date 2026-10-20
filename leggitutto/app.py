"""Finestra principale, pensata per essere usata da tastiera e con i lettori di schermo.

Usa wxPython perché crea controlli nativi di Windows e macOS: NVDA, JAWS, Assistente vocale
e VoiceOver li leggono correttamente, cosa che non accade con altre librerie grafiche.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import wx

from . import APP_NAME, AUTHOR, AUTHOR_EMAIL, COPYRIGHT, __version__, announce, external
from .help_text import guide
from .i18n import _, ngettext, set_language
from .model import Cancelled, ConversionError, Context
from .settings import ENCODINGS, LANGUAGES, UI_LANGUAGES, WHISPER_MODELS, Options


def mod_key() -> str:
    return _("Comando") if sys.platform == "darwin" else _("Control")


def open_path(path: Path):
    try:
        if sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as exc:
        wx.MessageBox(_("Impossibile aprire {target}: {exc}").format(target=path, exc=exc), APP_NAME, wx.OK | wx.ICON_ERROR)


def open_path_url(url: str):
    import webbrowser

    try:
        webbrowser.open(url)
    except Exception as exc:
        wx.MessageBox(_("Impossibile aprire {target}: {exc}").format(target=url, exc=exc), APP_NAME, wx.OK | wx.ICON_ERROR)


def labeled(parent, sizer, label, control, tooltip=""):
    """Etichetta + controllo. L'etichetta creata subito prima fa da nome per il lettore di schermo."""
    row = wx.BoxSizer(wx.HORIZONTAL)
    text = wx.StaticText(parent, label=label)
    row.Add(text, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
    control.MoveAfterInTabOrder(text)
    row.Add(control, 1, wx.EXPAND)
    sizer.Add(row, 0, wx.EXPAND | wx.ALL, 6)
    clean = label.replace("&", "").rstrip(":")
    control.SetName(clean)
    control.SetToolTip(tooltip or clean)
    return control


class FileDrop(wx.FileDropTarget):
    def __init__(self, frame):
        super().__init__()
        self.frame = frame

    def OnDropFiles(self, x, y, filenames):
        wx.CallAfter(self.frame.add_paths, filenames, True)
        return True


# ---------------------------------------------------------------------------
# Finestra delle opzioni

class OptionsDialog(wx.Dialog):
    def __init__(self, parent, opts: Options):
        super().__init__(parent, title=_("Opzioni"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.opts = opts
        book = wx.Notebook(self)
        book.SetName(_("Schede delle opzioni"))
        self.checks = {}

        # --- Generale: la lingua ha un'etichetta in entrambe le lingue, così la si trova sempre.
        page = wx.Panel(book)
        s = wx.BoxSizer(wx.VERTICAL)
        self.ui_language = labeled(page, s, "&Lingua / Language:", wx.Choice(page, choices=[d for _c, d in UI_LANGUAGES]),
                                   "Lingua dei menu e della guida / Language of menus and help")
        self.ui_language.SetSelection(next((i for i, (c, _d) in enumerate(UI_LANGUAGES) if c == opts.ui_language), 0))
        for key, label in [
            ("auto_convert_on_drop", _("Converti &subito i file trascinati o aggiunti")),
            ("open_when_done", _("&Apri il file di testo al termine della conversione")),
        ]:
            cb = wx.CheckBox(page, label=label)
            cb.SetValue(getattr(opts, key))
            s.Add(cb, 0, wx.ALL, 6)
            self.checks[key] = cb
        page.SetSizer(s)
        book.AddPage(page, _("Generale"))

        # --- Documenti
        page = wx.Panel(book)
        s = wx.BoxSizer(wx.VERTICAL)
        for key, label in [
            ("remove_page_numbers", _("Togli i &numeri di pagina")),
            ("remove_headers_footers", _("Togli &intestazioni e piè di pagina ripetuti")),
            ("remove_footnotes", _("Togli le &note a piè di pagina")),
            ("remove_note_markers", _("Togli i &richiami di nota nel testo (numerini, asterischi)")),
            ("reflow_paragraphs", _("Ricomponi i &paragrafi spezzati a fine riga")),
            ("remove_decorations", _("Togli &elementi superflui (puntini degli indici, righe decorative, menu delle pagine web)")),
            ("include_slide_notes", _("Includi le note del &relatore delle presentazioni")),
            ("ocr", _("Leggi il testo di &immagini e pagine scansionate (OCR)")),
        ]:
            cb = wx.CheckBox(page, label=label)
            cb.SetValue(getattr(opts, key))
            s.Add(cb, 0, wx.ALL, 6)
            self.checks[key] = cb
        self.ocr_langs = labeled(page, s, _("&Lingue per l'OCR (codici Tesseract separati da +):"),
                                 wx.TextCtrl(page, value=opts.ocr_languages),
                                 _("Per esempio ita+eng per italiano e inglese"))
        page.SetSizer(s)
        book.AddPage(page, _("Documenti"))

        # --- Audio e video
        page = wx.Panel(book)
        s = wx.BoxSizer(wx.VERTICAL)
        self.model = labeled(page, s, _("&Qualità della trascrizione:"),
                             wx.Choice(page, choices=[_(d) for _m, d in WHISPER_MODELS]))
        self.model.SetSelection(next((i for i, (m, _d) in enumerate(WHISPER_MODELS) if m == opts.whisper_model), 2))
        self.language = labeled(page, s, _("&Lingua parlata:"), wx.Choice(page, choices=[_(d) for _c, d in LANGUAGES]))
        self.language.SetSelection(next((i for i, (c, _d) in enumerate(LANGUAGES) if c == opts.language), 0))
        for key, label in [
            ("diarize", _("Indica &chi sta parlando (Persona 1, Persona 2...)")),
            ("timestamps", _("Aggiungi l'&orario di ogni intervento")),
            ("use_gpu", _("Usa la scheda &video NVIDIA, se presente (più veloce)")),
        ]:
            cb = wx.CheckBox(page, label=label)
            cb.SetValue(getattr(opts, key))
            s.Add(cb, 0, wx.ALL, 6)
            self.checks[key] = cb
        self.speakers = labeled(page, s, _("&Numero di persone che parlano (0 = riconoscimento automatico):"),
                                wx.SpinCtrl(page, min=0, max=30, initial=opts.num_speakers))
        page.SetSizer(s)
        book.AddPage(page, _("Audio e video"))

        # --- Salvataggio
        page = wx.Panel(book)
        s = wx.BoxSizer(wx.VERTICAL)
        self.same_folder = wx.CheckBox(page, label=_("Salva il testo nella &stessa cartella del file originale"))
        self.same_folder.SetValue(not opts.output_dir)
        s.Add(self.same_folder, 0, wx.ALL, 6)
        self.folder = labeled(page, s, _("Cartella di &destinazione:"),
                              wx.TextCtrl(page, value=opts.output_dir, style=wx.TE_READONLY))
        self.choose = wx.Button(page, label=_("&Scegli la cartella di destinazione..."))
        s.Add(self.choose, 0, wx.ALL, 6)
        self.encoding = labeled(page, s, _("&Codifica del testo:"), wx.Choice(page, choices=[_(d) for _e, d in ENCODINGS]))
        self.encoding.SetSelection(next((i for i, (e, _d) in enumerate(ENCODINGS) if e == opts.encoding), 0))
        self.wrap = labeled(page, s, _("&Vai a capo ogni tanti caratteri (0 = mai, consigliato):"),
                            wx.SpinCtrl(page, min=0, max=500, initial=opts.wrap_width))
        page.SetSizer(s)
        book.AddPage(page, _("Salvataggio"))

        self.choose.Bind(wx.EVT_BUTTON, self.on_choose)
        self.same_folder.Bind(wx.EVT_CHECKBOX, lambda e: self.update_folder())
        self.update_folder()

        main = wx.BoxSizer(wx.VERTICAL)
        main.Add(book, 1, wx.EXPAND | wx.ALL, 8)
        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        self.FindWindowById(wx.ID_OK).SetLabel("OK")
        self.FindWindowById(wx.ID_CANCEL).SetLabel(_("Annulla"))
        main.Add(buttons, 0, wx.EXPAND | wx.ALL, 8)
        self.SetSizerAndFit(main)
        self.SetMinSize((560, -1))
        self.CentreOnParent()
        book.SetFocus()

    def update_folder(self):
        enabled = not self.same_folder.GetValue()
        self.folder.Enable(enabled)
        self.choose.Enable(enabled)

    def on_choose(self, _event):
        with wx.DirDialog(self, _("Scegli la cartella in cui salvare i file di testo"), self.folder.GetValue()) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.folder.SetValue(dlg.GetPath())

    def apply(self):
        o = self.opts
        for key, cb in self.checks.items():
            setattr(o, key, cb.GetValue())
        o.ocr_languages = self.ocr_langs.GetValue().strip() or "ita+eng"
        o.whisper_model = WHISPER_MODELS[self.model.GetSelection()][0]
        o.language = LANGUAGES[self.language.GetSelection()][0]
        o.num_speakers = self.speakers.GetValue()
        o.encoding = ENCODINGS[self.encoding.GetSelection()][0]
        o.wrap_width = self.wrap.GetValue()
        o.output_dir = "" if self.same_folder.GetValue() else self.folder.GetValue()
        o.ui_language = UI_LANGUAGES[self.ui_language.GetSelection()][0]
        o.save()


# ---------------------------------------------------------------------------
# Finestra principale

class MainFrame(wx.Frame):
    def __init__(self, opts: Options):
        super().__init__(None, title=self.default_title(), size=(760, 620))
        self.opts = opts
        self.files: list[Path] = []
        self.worker: threading.Thread | None = None
        self.cancel_event = threading.Event()
        self.last_outputs: list[Path] = []
        self._last_announce = 0.0
        self._last_percent = -1

        panel = wx.Panel(self)
        self.panel = panel
        s = wx.BoxSizer(wx.VERTICAL)

        intro = wx.StaticText(panel, label=_(
            "Trascina qui i file da convertire in testo: documenti, libri, pagine web, immagini, audio o video. "
            "Oppure premi {mod}+O per sceglierli. F1 apre la guida.").format(mod=mod_key()))
        font = intro.GetFont()
        font.SetPointSize(font.GetPointSize() + 2)
        intro.SetFont(font)
        intro.Wrap(700)
        s.Add(intro, 0, wx.ALL | wx.EXPAND, 10)

        s.Add(wx.StaticText(panel, label=_("&File da convertire:")), 0, wx.LEFT | wx.TOP, 10)
        self.listbox = wx.ListBox(panel, style=wx.LB_EXTENDED | wx.LB_NEEDED_SB)
        self.listbox.SetName(_("File da convertire"))
        self.listbox.SetToolTip(_("Elenco dei file da convertire. Canc toglie i file selezionati."))
        s.Add(self.listbox, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        row = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_add = wx.Button(panel, label=_("&Aggiungi file..."))
        self.btn_folder = wx.Button(panel, label=_("Aggiungi &cartella..."))
        self.btn_remove = wx.Button(panel, label=_("&Togli dall'elenco"))
        self.btn_clear = wx.Button(panel, label=_("S&vuota l'elenco"))
        for b in (self.btn_add, self.btn_folder, self.btn_remove, self.btn_clear):
            row.Add(b, 0, wx.RIGHT, 6)
        s.Add(row, 0, wx.ALL, 10)

        row = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_convert = wx.Button(panel, label=_("Con&verti (F5)"))
        self.btn_stop = wx.Button(panel, label=_("&Interrompi"))
        self.btn_options = wx.Button(panel, label=_("&Opzioni..."))
        self.btn_open = wx.Button(panel, label=_("Apri l'&ultimo testo creato"))
        for b in (self.btn_convert, self.btn_stop, self.btn_options, self.btn_open):
            row.Add(b, 0, wx.RIGHT, 6)
        s.Add(row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.btn_convert.SetDefault()
        self.btn_stop.Disable()
        self.btn_open.Disable()

        s.Add(wx.StaticText(panel, label=_("Avanzamento:")), 0, wx.LEFT, 10)
        self.gauge = wx.Gauge(panel, range=1000)
        self.gauge.SetName(_("Avanzamento"))
        s.Add(self.gauge, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        self.status = wx.StaticText(panel, label=_("Pronto."))
        s.Add(self.status, 0, wx.ALL, 10)

        s.Add(wx.StaticText(panel, label=_("&Registro delle attività:")), 0, wx.LEFT, 10)
        self.log = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2, size=(-1, 140))
        self.log.SetName(_("Registro delle attività"))
        s.Add(self.log, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        panel.SetSizer(s)

        for window in (self, panel, self.listbox, self.log, intro, self.gauge):
            window.SetDropTarget(FileDrop(self))

        self._build_menu()
        self.btn_add.Bind(wx.EVT_BUTTON, self.on_add)
        self.btn_folder.Bind(wx.EVT_BUTTON, self.on_add_folder)
        self.btn_remove.Bind(wx.EVT_BUTTON, self.on_remove)
        self.btn_clear.Bind(wx.EVT_BUTTON, self.on_clear)
        self.btn_convert.Bind(wx.EVT_BUTTON, self.on_convert)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.on_stop)
        self.btn_options.Bind(wx.EVT_BUTTON, self.on_options)
        self.btn_open.Bind(wx.EVT_BUTTON, self.on_open_last)
        self.listbox.Bind(wx.EVT_KEY_DOWN, self.on_list_key)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.CreateStatusBar()
        self.SetStatusText(_("Pronto"))
        self.Centre()
        self.write_log(_("{app} {version} pronto. Trascina i file nella finestra o premi {mod}+O.").format(
            app=APP_NAME, version=__version__, mod=mod_key()))
        self.listbox.SetFocus()

    @staticmethod
    def default_title() -> str:
        return _("{app} - convertitore accessibile in testo").format(app=APP_NAME)

    # --- Menu e tasti rapidi
    def _build_menu(self):
        bar = wx.MenuBar()
        m = wx.Menu()
        self._menu(m, _("&Aggiungi file...") + "\tCtrl+O", self.on_add, wx.ID_OPEN)
        self._menu(m, _("Aggiungi &cartella...") + "\tCtrl+Shift+O", self.on_add_folder)
        m.AppendSeparator()
        self._menu(m, _("Con&verti") + "\tF5", self.on_convert)
        self._menu(m, _("&Interrompi") + "\tCtrl+I", self.on_stop)
        self._menu(m, _("Apri l'&ultimo testo creato") + "\tCtrl+L", self.on_open_last)
        self._menu(m, _("Apri la cartella dell'ultimo testo") + "\tCtrl+Shift+L", self.on_open_last_folder)
        m.AppendSeparator()
        self._menu(m, _("&Esci") + "\tCtrl+Q", lambda e: self.Close(), wx.ID_EXIT)
        bar.Append(m, _("&File"))
        m = wx.Menu()
        self._menu(m, _("&Opzioni...") + "\tCtrl+,", self.on_options, wx.ID_PREFERENCES)
        # Scelta rapida della lingua, con nomi sempre leggibili in entrambe le lingue.
        languages = wx.Menu()
        for code, name in UI_LANGUAGES:
            item = languages.AppendRadioItem(wx.ID_ANY, name)
            item.Check(code == self.opts.ui_language)
            self.Bind(wx.EVT_MENU, lambda e, c=code: self.change_language(c), item)
        m.AppendSubMenu(languages, "&Lingua / Language")
        bar.Append(m, _("&Strumenti"))
        m = wx.Menu()
        self._menu(m, _("&Guida") + "\tF1", self.on_help, wx.ID_HELP)
        self._menu(m, _("&Programmi aggiuntivi"), self.on_tools)
        self._menu(m, _("&Scrivi all'autore"), self.on_write_author)
        self._menu(m, _("&Informazioni su {app}").format(app=APP_NAME), self.on_about, wx.ID_ABOUT)
        bar.Append(m, _("&Aiuto"))
        self.SetMenuBar(bar)

    def _menu(self, menu, label, handler, wid=wx.ID_ANY):
        item = menu.Append(wid, label)
        self.Bind(wx.EVT_MENU, handler, item)
        return item

    # --- Annunci
    def say(self, text: str):
        announce.speak(text)

    def write_log(self, text: str):
        stamp = time.strftime("%H:%M:%S")
        self.log.AppendText(f"[{stamp}] {text}\n")

    # --- Gestione dell'elenco
    def add_paths(self, paths, dropped=False):
        added = 0
        for raw in paths:
            p = Path(raw)
            candidates = sorted(x for x in p.rglob("*") if x.is_file() and not x.name.startswith(".")) if p.is_dir() else [p]
            if not p.exists():
                self.write_log(_("File non trovato: {path}").format(path=p))
            for c in candidates:
                if c.is_file() and c not in self.files:
                    self.files.append(c)
                    self.listbox.Append(c.name)
                    added += 1
        if not added:
            return
        message = ngettext(added, "{n} file aggiunto all'elenco.", "{n} file aggiunti all'elenco.").format(n=added)
        self.write_log(message)
        self.SetStatusText(message)
        if self.opts.auto_convert_on_drop and not self.busy:
            self.start()
        else:
            self.say(message)

    @property
    def busy(self):
        return self.worker is not None and self.worker.is_alive()

    def on_add(self, _event):
        with wx.FileDialog(self, _("Scegli i file da convertire"), style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.add_paths(dlg.GetPaths())

    def on_add_folder(self, _event):
        with wx.DirDialog(self, _("Scegli una cartella: verranno convertiti tutti i file che contiene")) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.add_paths([dlg.GetPath()])

    def on_remove(self, _event):
        if self.busy:
            return
        for i in sorted(self.listbox.GetSelections(), reverse=True):
            self.listbox.Delete(i)
            del self.files[i]
        self.say(ngettext(len(self.files), "{n} file nell'elenco.", "{n} file nell'elenco.").format(n=len(self.files)))

    def on_clear(self, _event):
        if self.busy:
            return
        self.listbox.Clear()
        self.files.clear()
        self.say(_("Elenco svuotato."))

    def on_list_key(self, event):
        if event.GetKeyCode() in (wx.WXK_DELETE, wx.WXK_BACK, wx.WXK_NUMPAD_DELETE):
            self.on_remove(None)
        elif event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            self.on_convert(None)
        else:
            event.Skip()

    # --- Conversione
    def on_convert(self, _event):
        if self.busy:
            return
        if not self.files:
            wx.MessageBox(_("L'elenco è vuoto. Trascina dei file nella finestra o premi {mod}+O per sceglierli.").format(mod=mod_key()),
                          APP_NAME, wx.OK | wx.ICON_INFORMATION, self)
            return
        self.start()

    def start(self):
        self.cancel_event = threading.Event()
        self.btn_convert.Disable()
        self.btn_stop.Enable()
        self.btn_options.Disable()
        files = list(self.files)
        self.say(ngettext(len(files), "Conversione avviata: {n} file.", "Conversione avviata: {n} file.").format(n=len(files)))
        self.worker = threading.Thread(target=self.run_batch, args=(files, self.opts), daemon=True)
        self.worker.start()

    def on_stop(self, _event):
        if self.busy:
            self.cancel_event.set()
            self.status.SetLabel(_("Interruzione in corso..."))
            self.say(_("Interruzione in corso."))

    def run_batch(self, files, opts):
        from .converter import convert_file

        done, failed, outputs = [], [], []
        taken: set = set()
        total = len(files)
        for index, src in enumerate(files):
            if self.cancel_event.is_set():
                break
            wx.CallAfter(self.on_file_start, index, total, src)

            def progress(fraction, message, index=index):
                wx.CallAfter(self.on_progress, (index + fraction) / total, message, src.name)

            ctx = Context(progress=progress, ask_password=self.ask_password,
                          log=lambda m: wx.CallAfter(self.write_log, m), cancel_event=self.cancel_event)
            try:
                out = convert_file(src, opts, ctx, taken)
                outputs.append(out)
                done.append(src)
                wx.CallAfter(self.write_log, _("Creato: {path}").format(path=out))
            except Cancelled:
                wx.CallAfter(self.write_log, _("Conversione interrotta."))
                break
            except ConversionError as exc:
                failed.append((src, str(exc)))
                wx.CallAfter(self.write_log, _("Errore con {name}: {exc}").format(name=src.name, exc=exc))
            except Exception as exc:  # errori imprevisti: si continua con il file successivo
                failed.append((src, _("errore imprevisto: {exc}").format(exc=exc)))
                wx.CallAfter(self.write_log, _("Errore imprevisto con {name}: {exc}").format(name=src.name, exc=repr(exc)))
        wx.CallAfter(self.on_batch_done, done, failed, outputs, self.cancel_event.is_set())

    def ask_password(self, filename, attempt):
        """Chiamata dal thread di lavoro: mostra la richiesta di password e attende la risposta."""
        result = {}
        ready = threading.Event()

        def show():
            prompt = (_("Il file «{name}» è protetto da password.\nScrivi la password e premi Invio.")
                      if attempt == 0 else _("La password per «{name}» non è corretta. Riprova.")).format(name=filename)
            with wx.PasswordEntryDialog(self, prompt, _("Password richiesta")) as dlg:
                result["pw"] = dlg.GetValue() if dlg.ShowModal() == wx.ID_OK else None
            ready.set()

        wx.CallAfter(show)
        while not ready.wait(0.2):
            if self.cancel_event.is_set():
                return None
        return result.get("pw")

    def on_file_start(self, index, total, src):
        text = _("File {n} di {total}: {name}").format(n=index + 1, total=total, name=src.name)
        self.status.SetLabel(text)
        self.write_log(_("Conversione di {name}").format(name=src.name))
        for selected in self.listbox.GetSelections():
            self.listbox.Deselect(selected)
        if index < self.listbox.GetCount():
            self.listbox.SetSelection(index)
        self.say(text)
        self._last_percent = -1

    def on_progress(self, fraction, message, name):
        self.gauge.SetValue(int(fraction * 1000))
        percent = int(fraction * 100)
        label = f"{percent}% - {name}" + (f" - {message}" if message else "")
        self.status.SetLabel(label)
        self.SetStatusText(label)
        self.SetTitle(f"{percent}% - {APP_NAME}")
        # Un annuncio ogni 25% (al massimo uno ogni 20 secondi) per non sommergere l'utente.
        if percent // 25 > self._last_percent // 25 and time.time() - self._last_announce > 20:
            self._last_announce = time.time()
            if self._last_percent >= 0:
                self.say(_("{n} per cento").format(n=percent))
        self._last_percent = max(self._last_percent, percent)

    def on_batch_done(self, done, failed, outputs, cancelled):
        self.btn_convert.Enable()
        self.btn_stop.Disable()
        self.btn_options.Enable()
        self.gauge.SetValue(0 if cancelled else 1000)
        self.SetTitle(self.default_title())
        converted = set(done)
        for i in reversed(range(len(self.files))):
            if self.files[i] in converted:
                self.listbox.Delete(i)
                del self.files[i]
        if outputs:
            self.last_outputs = outputs
            self.btn_open.Enable()

        parts = []
        if cancelled:
            parts.append(_("Conversione interrotta."))
        if done:
            parts.append(ngettext(len(done), "{n} file convertito.", "{n} file convertiti.").format(n=len(done)))
        if failed:
            parts.append(ngettext(len(failed), "{n} file non convertito:", "{n} file non convertiti:").format(n=len(failed)))
            parts.extend(f"- {src.name}: {why}" for src, why in failed)
        if len(outputs) == 1:
            parts.append(_("Il testo è stato salvato in: {path}").format(path=outputs[0]))
        elif outputs:
            parts.append(_("I testi sono stati salvati in: {path}").format(path=outputs[0].parent))
        summary = "\n".join(parts) or _("Nessun file convertito.")
        self.status.SetLabel(summary.split("\n")[0])
        self.SetStatusText(summary.split("\n")[0])
        wx.Bell()

        if outputs and self.opts.open_when_done and not failed:
            open_path(outputs[0] if len(outputs) == 1 else outputs[0].parent)
            self.say(summary.split("\n")[0])
            return
        style = wx.ICON_WARNING if failed or cancelled else wx.ICON_INFORMATION
        if outputs:
            question = _("Vuoi aprirlo adesso?") if len(outputs) == 1 else _("Vuoi aprire la cartella adesso?")
            dlg = wx.MessageDialog(self, summary + "\n\n" + question, _("Conversione terminata"),
                                   wx.YES_NO | wx.YES_DEFAULT | style)
            dlg.SetYesNoLabels(_("&Apri il testo") if len(outputs) == 1 else _("&Apri la cartella"), _("&Chiudi"))
            if dlg.ShowModal() == wx.ID_YES:
                open_path(outputs[0] if len(outputs) == 1 else outputs[0].parent)
            dlg.Destroy()
        else:
            wx.MessageBox(summary, _("Conversione terminata"), wx.OK | style, self)
        self.listbox.SetFocus()

    def on_open_last(self, _event):
        if self.last_outputs:
            open_path(self.last_outputs[-1])

    def on_open_last_folder(self, _event):
        if self.last_outputs:
            open_path(self.last_outputs[-1].parent)

    # --- Finestre di dialogo
    def on_options(self, _event):
        if self.busy:
            wx.MessageBox(_("Attendi la fine della conversione per cambiare le opzioni."), APP_NAME, wx.OK, self)
            return
        previous = self.opts.ui_language
        with OptionsDialog(self, self.opts) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            dlg.apply()
        self.write_log(_("Opzioni salvate."))
        if self.opts.ui_language != previous:
            wx.CallAfter(self.change_language, self.opts.ui_language, True)

    def change_language(self, code: str, force: bool = False):
        """Ricrea la finestra nella nuova lingua, conservando l'elenco dei file."""
        if code == self.opts.ui_language and not force:
            return
        if self.busy:
            wx.MessageBox(_("Attendi la fine della conversione per cambiare le opzioni."), APP_NAME, wx.OK, self)
            return
        self.opts.ui_language = code
        self.opts.save()
        set_language(code)
        frame = MainFrame(self.opts)
        frame.files = list(self.files)
        frame.listbox.Set([f.name for f in self.files])
        frame.last_outputs = self.last_outputs
        frame.btn_open.Enable(bool(self.last_outputs))
        frame.SetPosition(self.GetPosition())
        frame.SetSize(self.GetSize())
        app = wx.GetApp()
        app.frame = frame
        app.SetTopWindow(frame)
        frame.Show()
        frame.Raise()
        frame.listbox.SetFocus()
        self.Destroy()
        frame.say(_("Lingua cambiata: italiano.") if code == "it" else _("Lingua cambiata: inglese."))

    def show_text(self, title, text):
        dlg = wx.Dialog(self, title=title, size=(700, 560), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        s = wx.BoxSizer(wx.VERTICAL)
        ctrl = wx.TextCtrl(dlg, value=text, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        ctrl.SetName(title)
        s.Add(ctrl, 1, wx.EXPAND | wx.ALL, 8)
        close = wx.Button(dlg, wx.ID_CANCEL, _("&Chiudi"))
        s.Add(close, 0, wx.ALIGN_RIGHT | wx.ALL, 8)
        dlg.SetSizer(s)
        dlg.SetEscapeId(wx.ID_CANCEL)
        ctrl.SetFocus()
        ctrl.SetInsertionPoint(0)
        dlg.ShowModal()
        dlg.Destroy()

    def on_help(self, _event):
        self.show_text(_("Guida di {app}").format(app=APP_NAME), guide())

    def on_tools(self, _event):
        from . import ocr

        lines = []
        tess = external.find_program("tesseract")
        if tess and ocr.available():
            try:
                langs = ocr.language_string(self.opts.ocr_languages)
            except Exception:
                langs = "?"
            lines.append(_("Tesseract OCR: installato ({path}). Lingue usate: {langs}.").format(path=tess, langs=langs))
            if "ita" not in langs:
                lines.append("  " + _("Attenzione: manca la lingua italiana di Tesseract (ita)."))
        else:
            lines.append(_("Tesseract OCR: non installato. Serve per immagini e PDF scansionati."))
        for name, label, use in [("soffice", "LibreOffice", _("vecchi file .doc, .ppt e formati rari")),
                                 ("ebook-convert", "Calibre", _("eBook MOBI, AZW3, LIT e simili")),
                                 ("djvutxt", "DjVuLibre", _("file DjVu"))]:
            path = external.find_program(name)
            lines.append(f"{label}: " + (_("installato ({path}).").format(path=path) if path
                                         else _("non installato. Serve per {use}.").format(use=use)))
        lines.append("")
        lines.append(_("I modelli per audio e video vengono scaricati automaticamente al primo utilizzo."))
        self.show_text(_("Programmi aggiuntivi"), "\n".join(lines))

    def on_about(self, _event):
        self.show_text(_("Informazioni su {app}").format(app=APP_NAME), (
            f"{APP_NAME} {__version__}\n\n"
            + _("Converte qualsiasi file in testo semplice accessibile, per la lettura con sintesi vocale "
                "e display braille.") + "\n\n"
            + _("Creato da {author}").format(author=AUTHOR) + "\n"
            + _("Posta elettronica: {email}").format(email=AUTHOR_EMAIL) + "\n"
            + f"{COPYRIGHT}\n\n"
            + _("Usa software libero: PyMuPDF, Tesseract, faster-whisper (modelli Whisper di OpenAI), "
                "sherpa-onnx con i modelli pyannote e WeSpeaker, wxPython.")))

    def on_write_author(self, _event):
        open_path_url(f"mailto:{AUTHOR_EMAIL}?subject={APP_NAME}%20{__version__}")

    def on_close(self, event):
        if self.busy:
            if wx.MessageBox(_("È in corso una conversione. Vuoi interromperla e uscire?"), APP_NAME,
                             wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self) != wx.YES:
                event.Veto()
                return
            self.cancel_event.set()
        self.opts.save()
        event.Skip()


class LeggiTuttoApp(wx.App):
    def __init__(self, initial_files):
        self.initial_files = initial_files
        self.frame = None
        super().__init__(redirect=False)

    def OnInit(self):
        self.SetAppName(APP_NAME)
        opts = Options.load()
        set_language(opts.ui_language)
        self.frame = MainFrame(opts)
        self.frame.Show()
        self.SetTopWindow(self.frame)
        if self.initial_files:
            wx.CallAfter(self.frame.add_paths, self.initial_files, True)
        return True

    # macOS: file trascinati sull'icona nel Dock o aperti con "Apri con".
    def MacOpenFiles(self, filenames):
        if self.frame is not None:
            self.frame.add_paths(filenames, True)

    def MacReopenApp(self):
        if self.frame is not None:
            self.frame.Raise()


def main(argv=None):
    app = LeggiTuttoApp([a for a in (argv or []) if os.path.exists(a)])
    app.MainLoop()
