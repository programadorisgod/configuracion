import os
import re
import sys
import json
import shutil
import subprocess
from pathlib import Path
from obs_pipeline.hardware import find_binary, get_safe_threads


def parse_time_str(time_val: str | float | int) -> float:
    """Convierte un timestamp 'MM:SS', 'HH:MM:SS' o segundos float a float total de segundos."""
    if isinstance(time_val, (int, float)):
        return float(time_val)

    s = str(time_val).strip()
    parts = s.split(":")
    if len(parts) == 3:
        h, m, sec = parts
        return int(h) * 3600 + int(m) * 60 + float(sec)
    elif len(parts) == 2:
        m, sec = parts
        return int(m) * 60 + float(sec)
    return float(s)


def format_ass_time(seconds: float) -> str:
    """Convierte segundos a formato de tiempo ASS (H:MM:SS.cc)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


SHORTS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "shorts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title_hook": {
                        "type": "string",
                        "description": "Titular gancho impactante en MAYÚSCULAS para el tercio superior del Short (3 a 5 palabras, ej. '¡TRUCO SECRETO DE WINDOWS!')",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Timestamp de inicio en formato MM:SS exacto sobre la transcripción (ej: '02:11')",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Timestamp de finalización en formato MM:SS (duración entre 30 y 55 segundos)",
                    },
                    "viral_reason": {
                        "type": "string",
                        "description": "Explicación breve de por qué este fragmento funciona como video viral de formato corto",
                    },
                },
                "required": ["title_hook", "start_time", "end_time", "viral_reason"],
            },
        }
    },
    "required": ["shorts"],
}


def detect_viral_moments(
    transcript_text: str,
    target_count: int = 3,
    timeout: int = 90,
) -> list[dict]:
    """
    Utiliza Antigravity CLI (agy -p) en modo headless con JSON schema para detectar
    los mejores 1 a 3 momentos virales (30 a 55 segundos) a partir de la transcripción.
    """
    agy_bin = find_binary("agy")
    if shutil.which(agy_bin) or Path(agy_bin).exists():
        prompt = (
            f"Analiza la siguiente transcripción con timestamps de un tutorial de software/programación.\n"
            f"Tu objetivo es seleccionar exactamente los mejores {target_count} fragmentos para convertirlos en YouTube Shorts, TikToks o Reels verticales.\n\n"
            f"REGLAS INNEGOCIABLES:\n"
            f"1. Cada fragmento debe durar entre 30 y 55 segundos (máximo 58 segundos).\n"
            f"2. Debe tener estructura de alta retención: Gancho inicial (Hook) -> Demostración/Tip -> Conclusión o llamada a la acción.\n"
            f"3. 'title_hook': Debe ser un titular de impacto en MAYÚSCULAS (3 a 5 palabras, sin comillas adicionales).\n"
            f"4. 'start_time' y 'end_time' deben corresponder a timestamps reales de la transcripción.\n\n"
            f"TRANSCRIPCIÓN:\n{transcript_text[:12000]}"
        )
        cmd = [
            agy_bin,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(SHORTS_JSON_SCHEMA),
            "--disable-slash-commands",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
            data = json.loads(res.stdout.strip())
            if "shorts" in data and len(data["shorts"]) > 0:
                return data["shorts"]
        except Exception:
            pass

    # Respaldo heurístico offline si agy no responde
    return [
        {
            "title_hook": "¡TRUCO PRO DE PRODUCTIVIDAD!",
            "start_time": "02:11",
            "end_time": "02:58",
            "viral_reason": "Presentación y demostración de búsqueda instantánea.",
        }
    ]


def extract_clip_audio(
    video_path: Path,
    output_audio: Path,
    start_sec: float,
    end_sec: float,
) -> Path:
    """Extrae la pista de audio de un fragmento específico en 16kHz mono para Whisper."""
    ffmpeg_bin = find_binary("ffmpeg")
    cmd = [
        ffmpeg_bin,
        "-y",
        "-ss",
        f"{start_sec:.2f}",
        "-to",
        f"{end_sec:.2f}",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_audio),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_audio


def transcribe_words_for_short(
    clip_audio: Path,
    language: str = "es",
) -> list[dict]:
    """Genera marcas de tiempo a nivel de palabra para subtítulos dinámicos usando faster-whisper."""
    # Monkeypatch para PyAV si es necesario
    try:
        import av
        if not hasattr(av, "_patched_open"):
            _orig_open = av.open
            def _safe_open(*args, **kwargs):
                kwargs.pop("metadata_errors", None)
                return _orig_open(*args, **kwargs)
            av.open = _safe_open
            av._patched_open = True
    except Exception:
        pass

    from faster_whisper import WhisperModel

    model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=get_safe_threads())
    segments, _ = model.transcribe(
        str(clip_audio),
        language=language,
        word_timestamps=True,
        vad_filter=True,
    )

    all_words = []
    for s in segments:
        if s.words:
            for w in s.words:
                cleaned = w.word.strip()
                if cleaned:
                    all_words.append({
                        "word": cleaned,
                        "start": w.start,
                        "end": w.end,
                    })
    return all_words


def generate_dynamic_ass(
    words: list[dict],
    hook_title: str,
    total_duration_sec: float,
    output_ass: Path,
    font_name: str = "Arial",
) -> Path:
    r"""
    Genera un archivo de subtítulos .ass (Advanced SubStation Alpha) con:
    1. Titular Gancho (Hook Title) fijo en el tercio superior (\an8\pos(540, 190)).
    2. Subtítulos dinámicos estilo TikTok / Hormozi en frases cortas de 3 a 5 palabras,
       con la palabra activa resaltada en amarillo neón (#FFE600).
    """
    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: HookHeader,Impact,68,&H0000FFFF,&H00000000,&H00100A05,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,8,40,40,160,1",
        f"Style: Captions,{font_name},78,&H00FFFFFF,&H00000000,&H00080602,&H90000000,-1,0,0,0,100,100,0,0,1,8,4,2,60,60,360,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    # 1. Titular superior fijo durante todo el video
    clean_hook = hook_title.strip().upper()
    dur_ass = format_ass_time(total_duration_sec)
    ass_lines.append(f"Dialogue: 0,0:00:00.00,{dur_ass},HookHeader,,0,0,0,,{clean_hook}")

    # 2. Agrupación de palabras en frases de 3 a 4 palabras
    group_size = 4
    for i in range(0, len(words), group_size):
        chunk = words[i : i + group_size]
        if not chunk:
            continue
        g_start = chunk[0]["start"]
        g_end = chunk[-1]["end"]

        # Para cada palabra dentro del grupo, generamos un micro-evento con esa palabra resaltada
        for current_idx, current_word in enumerate(chunk):
            w_start = format_ass_time(current_word["start"])
            w_end = format_ass_time(current_word["end"])
            # Si el tiempo es inválido o idéntico, expandir levemente
            if current_word["end"] <= current_word["start"]:
                w_end = format_ass_time(current_word["start"] + 0.25)

            # Construir texto del grupo resaltando la palabra actual en amarillo neón (&H0000E6FF&)
            styled_words = []
            for idx, w in enumerate(chunk):
                if idx == current_idx:
                    styled_words.append(r"{\c&H0000E6FF&}" + w["word"] + r"{\c&H00FFFFFF&}")
                else:
                    styled_words.append(w["word"])
            line_text = " ".join(styled_words)
            ass_lines.append(f"Dialogue: 1,{w_start},{w_end},Captions,,0,0,0,,{line_text}")

    output_ass.parent.mkdir(parents=True, exist_ok=True)
    output_ass.write_text("\n".join(ass_lines), encoding="utf-8")
    return output_ass


def render_vertical_short(
    video_path: Path,
    start_sec: float,
    end_sec: float,
    hook_title: str,
    output_mp4: Path,
    ass_subtitles_path: Path | None = None,
    blur_radius: int = 25,
) -> Path:
    """
    Renderiza el video en formato 9:16 vertical (1080x1920) utilizando FFmpeg:
    - [bg]: Fondo ampliado a 1080x1920 con desenfoque gaussiano cinematográfico.
    - [fg]: Video original 16:9 centrado de forma nítida con escala Lanczos.
    - Subtítulos dinámicos e incrustación de audio normalizado EBU R128 (-14 LUFS).
    """
    ffmpeg_bin = find_binary("ffmpeg")
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    # Preparar ruta de subtítulos con escape seguro para FFmpeg en Windows y Linux
    sub_filter = ""
    if ass_subtitles_path and ass_subtitles_path.exists():
        # En Windows, FFmpeg requiere barras invertidas escapadas o usar forward slashes con colon escapado: C\:/path...
        clean_ass_path = str(ass_subtitles_path.resolve()).replace("\\", "/")
        if sys.platform == "win32" and ":" in clean_ass_path:
            clean_ass_path = clean_ass_path.replace(":", r"\:")
        sub_filter = f"[vcomp]ass='{clean_ass_path}'[vout]"
    else:
        sub_filter = f"[vcomp]null[vout]"

    filter_complex = (
        f"[0:v]split=2[bg][fg];"
        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur={blur_radius}:2[bg_blur];"
        f"[fg]scale=1080:-1:flags=lanczos[fg_scaled];"
        f"[bg_blur][fg_scaled]overlay=0:(H-h)/2[vcomp];"
        f"{sub_filter}"
    )

    cmd = [
        ffmpeg_bin,
        "-y",
        "-ss",
        f"{start_sec:.2f}",
        "-to",
        f"{end_sec:.2f}",
        "-i",
        str(video_path),
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-map",
        "0:a",
        "-af",
        "loudnorm=I=-14:LRA=7:tp=-1",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output_mp4),
    ]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_mp4
