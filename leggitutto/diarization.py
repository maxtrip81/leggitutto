"""Riconoscimento di chi sta parlando (diarizzazione), interamente sul computer dell'utente.

Usa sherpa-onnx con due piccoli modelli (circa 33 MB in tutto) scaricati al primo uso:
un modello pyannote che segmenta il parlato e un modello che riconosce le voci.
"""

from __future__ import annotations

import os
import shutil
import ssl
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from .model import Context
from .settings import models_dir

_BASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download"
SEGMENTATION_URL = f"{_BASE}/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2"
EMBEDDING_URL = f"{_BASE}/speaker-recongition-models/wespeaker_en_voxceleb_resnet34_LM.onnx"


def _ssl_context():
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def download(url: str, dest: Path, ctx: Context, label: str):
    dest.parent.mkdir(parents=True, exist_ok=True)
    ctx.log(f"Scaricamento di {label} (solo la prima volta)...")
    tmp = dest.with_suffix(dest.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "LeggiTutto"})
    with urllib.request.urlopen(request, context=_ssl_context(), timeout=60) as response, open(tmp, "wb") as out:
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        while True:
            ctx.check_cancel()
            chunk = response.read(1 << 16)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                ctx.progress(done / total, f"Scaricamento di {label}: {done * 100 // total}%")
    os.replace(tmp, dest)


def ensure_models(ctx: Context) -> tuple[Path, Path]:
    folder = models_dir() / "voci"
    segmentation = folder / "segmentazione.onnx"
    embedding = folder / "riconoscimento-voci.onnx"
    folder.mkdir(parents=True, exist_ok=True)
    if not segmentation.is_file():
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "seg.tar.bz2"
            download(SEGMENTATION_URL, archive, ctx, "modello di segmentazione delle voci")
            with tarfile.open(archive) as tar:
                member = next(m for m in tar.getmembers() if m.name.endswith("/model.onnx"))
                partial = segmentation.with_suffix(".part")
                with tar.extractfile(member) as src, open(partial, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                os.replace(partial, segmentation)
    if not embedding.is_file():
        download(EMBEDDING_URL, embedding, ctx, "modello di riconoscimento delle voci")
    return segmentation, embedding


def diarize(samples, ctx: Context, num_speakers: int = 0, progress_base: float = 0.0, progress_span: float = 1.0):
    """Restituisce una lista di (inizio, fine, numero_voce) ordinata nel tempo.

    ``samples`` è audio mono float32 a 16 kHz.
    """
    import sherpa_onnx

    segmentation, embedding = ensure_models(ctx)
    threads = max(1, min(8, (os.cpu_count() or 2) - 1))
    config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
        segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
            pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(model=str(segmentation)),
            num_threads=threads,
        ),
        embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=str(embedding), num_threads=threads),
        clustering=sherpa_onnx.FastClusteringConfig(num_clusters=num_speakers if num_speakers > 0 else -1, threshold=0.33),
        min_duration_on=0.3,
        min_duration_off=0.5,
    )
    if not config.validate():
        raise RuntimeError("configurazione dei modelli delle voci non valida")
    engine = sherpa_onnx.OfflineSpeakerDiarization(config)

    def callback(done, total):
        if ctx.cancel_event.is_set():
            return 1  # interrompe l'elaborazione
        if total:
            ctx.progress(progress_base + progress_span * done / total, "Riconoscimento delle voci")
        return 0

    result = engine.process(samples, callback=callback).sort_by_start_time()
    ctx.check_cancel()
    return [(seg.start, seg.end, seg.speaker) for seg in result]
