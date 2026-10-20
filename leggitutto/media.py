"""Trascrizione di audio e video in testo, con l'indicazione di chi parla.

Il riconoscimento vocale (Whisper, tramite faster-whisper) e quello delle voci
funzionano sul computer: nessun file viene inviato a servizi esterni.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path

from .i18n import _, ngettext
from .model import Cancelled, ConversionError, Context, Extracted
from .settings import LANGUAGES, Options, models_dir

SAMPLE_RATE = 16000

# Frasi che Whisper "inventa" nei silenzi, imparate dai sottotitoli presenti in rete.
_HALLUCINATIONS = re.compile(
    r"^\s*(sottotitoli (creati|e revisione|a cura|realizzati).*|.*amara\.org.*|.*qtss.*|"
    r"grazie (a tutti )?per (la visione|l'ascolto|aver guardato)[.!]?|iscriviti al canale.*|"
    r"subtitles by.*|thanks for watching[.!]?|untertitel.*|sous-titr.*)\s*$",
    re.I,
)

_models: dict[tuple, object] = {}
_models_lock = threading.Lock()


@dataclass
class Word:
    start: float
    end: float
    text: str
    speaker: int = -1


def load_whisper(name: str, use_gpu: bool, ctx: Context):
    from faster_whisper import WhisperModel

    key = (name, use_gpu)
    with _models_lock:
        if key in _models:
            return _models[key]
        ctx.log(_("Caricamento del modello di riconoscimento vocale «{name}». "
                  "Al primo utilizzo viene scaricato da Internet: può richiedere alcuni minuti.").format(name=name))
        ctx.progress(0.0, _("Preparazione del riconoscimento vocale"))
        kwargs = dict(download_root=str(models_dir() / "whisper"), cpu_threads=max(1, min(8, os.cpu_count() or 4)))
        try:
            if use_gpu:
                model = WhisperModel(name, device="cuda", compute_type="float16", **kwargs)
            else:
                model = WhisperModel(name, device="cpu", compute_type="int8", **kwargs)
        except Exception as exc:
            if use_gpu:
                ctx.warn(_("scheda video non utilizzabile ({exc}), uso il processore.").format(exc=exc))
                model = WhisperModel(name, device="cpu", compute_type="int8", **kwargs)
            else:
                raise ConversionError(_(
                    "impossibile caricare il modello vocale «{name}». Controlla la connessione a Internet "
                    "(serve solo la prima volta). Dettagli: {exc}").format(name=name, exc=exc)) from exc
        _models.clear()  # un solo modello in memoria alla volta
        _models[key] = model
        return model


def _clock(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def _duration_words(seconds: float) -> str:
    seconds = int(round(seconds))
    h, m, s = seconds // 3600, seconds % 3600 // 60, seconds % 60
    parts = []
    if h:
        parts.append(ngettext(h, "{n} ora", "{n} ore").format(n=h))
    if m:
        parts.append(ngettext(m, "{n} minuto", "{n} minuti").format(n=m))
    if s or not parts:
        parts.append(ngettext(s, "{n} secondo", "{n} secondi").format(n=s))
    return (" %s " % _("e")).join([", ".join(parts[:-1]), parts[-1]]) if len(parts) > 1 else parts[0]


def assign_speakers(words: list[Word], turns: list[tuple[float, float, int]]):
    """Associa a ogni parola la voce che parla in quel momento, poi corregge i salti isolati."""
    if not turns:
        return
    j = 0
    for word in words:
        while j < len(turns) - 1 and turns[j][1] < word.start:
            j += 1
        best, best_overlap = None, 0.0
        for k in range(max(0, j - 2), min(len(turns), j + 3)):
            start, end, spk = turns[k]
            overlap = min(end, word.end) - max(start, word.start)
            if overlap > best_overlap:
                best, best_overlap = spk, overlap
        if best is None:  # parola in una pausa: la voce più vicina
            mid = (word.start + word.end) / 2
            best = min(turns[max(0, j - 2):j + 3], key=lambda t: min(abs(t[0] - mid), abs(t[1] - mid)))[2]
        word.speaker = best

    # Brevi "salti" di una o due parole fra due tratti della stessa voce sono quasi sempre errori.
    i = 0
    while i < len(words):
        k = i
        while k < len(words) and words[k].speaker == words[i].speaker:
            k += 1
        run = words[i:k]
        short = len(run) <= 2 and (run[-1].end - run[0].start) < 1.0
        if short and i > 0 and k < len(words) and words[i - 1].speaker == words[k].speaker:
            for w in run:
                w.speaker = words[i - 1].speaker
        elif short and i == 0 and k < len(words):
            for w in run:
                w.speaker = words[k].speaker
        i = k


def _paragraphs(words: list[Word], speaker_labels: bool) -> list[tuple[float, int, str]]:
    """Raggruppa le parole in interventi (cambio di voce) e paragrafi (pause lunghe)."""
    out: list[tuple[float, int, list[Word]]] = []
    for word in words:
        if out:
            start, spk, group = out[-1]
            pause = word.start - group[-1].end
            length = sum(len(w.text) for w in group)
            sentence_end = group[-1].text.rstrip().endswith((".", "?", "!"))
            same = (not speaker_labels or spk == word.speaker)
            if same and not (pause > 2.0 or (length > 700 and sentence_end) or (pause > 1.0 and sentence_end and length > 300)):
                group.append(word)
                continue
        out.append((word.start, word.speaker, [word]))
    return [(start, spk, "".join(w.text for w in group).strip()) for start, spk, group in out]


def decode_audio(path: Path, ctx: Context):
    """Estrae l'audio di qualsiasi file audio o video come mono a 16 kHz (numeri float32)."""
    import av
    import numpy as np

    try:
        container = av.open(str(path))
    except Exception as exc:
        raise ConversionError(_("il file audio o video non si apre ({exc}).").format(exc=exc)) from exc
    with container:
        if not container.streams.audio:
            raise ConversionError(_("il file non contiene una traccia audio."))
        stream = container.streams.audio[0]
        total = float(container.duration or 0) / 1_000_000
        resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
        chunks = []
        try:
            for frame in container.decode(stream):
                for out in resampler.resample(frame):
                    chunks.append(out.to_ndarray().reshape(-1).copy())
                if total and frame.time and len(chunks) % 200 == 0:
                    ctx.progress(0.0, _("Estrazione dell'audio: {percent}%").format(percent=min(99, int(frame.time * 100 / total))))
            for out in resampler.resample(None):
                chunks.append(out.to_ndarray().reshape(-1).copy())
        except av.error.FFmpegError as exc:
            if not chunks:
                raise ConversionError(_("traccia audio non leggibile ({exc}).").format(exc=exc)) from exc
            ctx.warn(_("la parte finale del file è danneggiata: trascritto solo l'inizio."))
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(chunks).astype(np.float32) / 32768.0


def transcribe(path: Path, opts: Options, ctx: Context) -> Extracted:
    ctx.progress(0.0, _("Estrazione dell'audio"))
    audio = decode_audio(path, ctx)
    duration = len(audio) / SAMPLE_RATE
    if duration < 0.3:
        raise ConversionError(_("la traccia audio è vuota."))
    ctx.log(_("Durata: {duration}.").format(duration=_duration_words(duration)))

    model = load_whisper(opts.whisper_model, opts.use_gpu, ctx)
    share = 0.8 if opts.diarize else 1.0
    segments, info = model.transcribe(
        audio,
        language=opts.language or None,
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        word_timestamps=True,
        condition_on_previous_text=False,
    )
    language = _(dict(LANGUAGES).get(info.language, info.language))
    if not opts.language:
        ctx.log(_("Lingua riconosciuta: {language}.").format(language=language))

    words: list[Word] = []
    previous = ""
    repeats = 0
    for seg in segments:
        ctx.progress(share * min(seg.end / duration, 1.0), _("Trascrizione: {done} di {total}").format(done=_clock(seg.end), total=_clock(duration)))
        text = seg.text.strip()
        if not text or _HALLUCINATIONS.match(text):
            continue
        if seg.no_speech_prob > 0.7 and seg.avg_logprob < -1.0:
            continue
        repeats = repeats + 1 if text == previous else 0
        previous = text
        if repeats >= 2:  # Whisper a volte ripete la stessa frase all'infinito
            continue
        if seg.words:
            words.extend(Word(w.start, w.end, w.word) for w in seg.words)
        else:
            words.append(Word(seg.start, seg.end, " " + text))

    if not words:
        return Extracted(final=_("Nel file «{name}» non è stato riconosciuto parlato.").format(name=path.name) + "\n")

    speakers = 1
    if opts.diarize:
        try:
            from .diarization import diarize

            turns = diarize(audio, ctx, opts.num_speakers, progress_base=share, progress_span=1 - share)
            assign_speakers(words, turns)
            order: dict[int, int] = {}
            for w in words:
                if w.speaker >= 0 and w.speaker not in order:
                    order[w.speaker] = len(order) + 1
            for w in words:
                w.speaker = order.get(w.speaker, 0)
            speakers = len(order) or 1
        except (Cancelled, ConversionError):
            raise
        except Exception as exc:
            ctx.warn(_("non è stato possibile distinguere le voci ({exc}); trascrizione senza nomi.").format(exc=exc))

    labels = opts.diarize and speakers > 1
    lines = [
        _("Trascrizione di «{name}»").format(name=path.name),
        _("Durata: {duration}. Lingua: {language}.").format(duration=_duration_words(duration), language=language)
        + (" " + _("Voci diverse riconosciute: {n}.").format(n=speakers) if opts.diarize else ""),
        "",
    ]
    for start, spk, text in _paragraphs(words, labels):
        prefix = f"[{_clock(start)}] " if opts.timestamps else ""
        who = _("Persona {n}").format(n=spk) + ": " if labels else ""
        lines.append(prefix + who + text)
        lines.append("")
    ctx.progress(1.0, _("Trascrizione completata"))
    return Extracted(final="\n".join(lines))
