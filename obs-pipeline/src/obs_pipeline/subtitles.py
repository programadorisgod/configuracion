import gc
from pathlib import Path

# Compatibilidad con PyAV >= 19 (elimina 'metadata_errors' obsoleto)
try:
    import av
    _orig_av_open = av.open

    def _safe_av_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_av_open(*args, **kwargs)

    av.open = _safe_av_open
except Exception:
    pass


def format_timestamp_srt(seconds: float) -> str:
    """Convierte segundos a formato HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """Convierte segundos a formato HH:MM:SS.mmm"""
    return format_timestamp_srt(seconds).replace(",", ".")


def format_timestamp_simple(seconds: float) -> str:
    """Convierte segundos a formato MM:SS o HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def generate_subtitles(
    audio_path: Path,
    output_dir: Path,
    subtitles_cfg: dict,
    language: str = "es",
    cpu_threads: int = 3,
) -> dict:
    """
    Transcribe el audio usando faster-whisper (int8 en CPU) y genera archivos .srt, .vtt y .txt.
    Libera la memoria RAM inmediatamente al terminar.
    """
    from faster_whisper import WhisperModel

    model_size = subtitles_cfg.get("model_size", "base")
    compute_type = subtitles_cfg.get("compute_type", "int8")
    vad_filter = subtitles_cfg.get("vad_filter", True)

    # Inicializar modelo Whisper limitado a cpu_threads seguros
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type=compute_type,
        cpu_threads=cpu_threads,
    )

    lang_arg = language if language != "auto" else None
    segments, info = model.transcribe(
        str(audio_path),
        language=lang_arg,
        vad_filter=vad_filter,
    )

    srt_lines = []
    vtt_lines = ["WEBVTT\n"]
    txt_lines = []
    plain_text_parts = []
    segment_data = []

    for idx, seg in enumerate(segments, start=1):
        text = seg.text.strip()
        if not text:
            continue

        start_srt = format_timestamp_srt(seg.start)
        end_srt = format_timestamp_srt(seg.end)
        start_vtt = format_timestamp_vtt(seg.start)
        end_vtt = format_timestamp_vtt(seg.end)
        start_simple = format_timestamp_simple(seg.start)

        # Formato SRT
        srt_lines.append(f"{idx}\n{start_srt} --> {end_srt}\n{text}\n")

        # Formato VTT
        vtt_lines.append(f"{idx}\n{start_vtt} --> {end_vtt}\n{text}\n")

        # Formato TXT con marcas de tiempo legibles
        txt_lines.append(f"[{start_simple}] {text}")
        plain_text_parts.append(text)
        segment_data.append({"start": seg.start, "end": seg.end, "text": text})

    # Liberación explícita de memoria RAM para no penalizar a gflow / Chromium
    del model
    gc.collect()

    # Guardar archivos
    srt_path = output_dir / "subtitulos.srt"
    vtt_path = output_dir / "subtitulos.vtt"
    txt_path = output_dir / "transcripcion.txt"

    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
    vtt_path.write_text("\n".join(vtt_lines), encoding="utf-8")
    txt_path.write_text("\n".join(txt_lines), encoding="utf-8")

    return {
        "srt_path": srt_path,
        "vtt_path": vtt_path,
        "txt_path": txt_path,
        "duration": info.duration if hasattr(info, "duration") else 0,
        "language": info.language if hasattr(info, "language") else language,
        "full_text": " ".join(plain_text_parts),
        "segments": segment_data,
    }
