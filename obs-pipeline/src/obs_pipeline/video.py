import re
import subprocess
from pathlib import Path
from obs_pipeline.hardware import find_binary


def detect_silence_trim(
    target_file: Path,
    silence_db: float = -45.0,
    silence_dur: float = 0.8,
    max_start_trim: float = 15.0,
) -> tuple[float, float | None]:
    """
    Detecta segundos de silencio al inicio y final del audio/video usando silencedetect.
    Para máxima precisión contra ruido de fondo, se recomienda pasar el archivo de audio post-DSP.
    Retorna (trim_start_segundos, trim_end_segundos).
    """
    ffmpeg_bin = find_binary("ffmpeg")
    cmd = [
        ffmpeg_bin,
        "-i", str(target_file),
        "-af", f"silencedetect=noise={silence_db}dB:d={silence_dur}",
        "-f", "null",
        "-"
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        stderr = proc.stderr
    except subprocess.CalledProcessError as e:
        stderr = e.stderr

    start_trim = 0.0
    end_trim = None

    # Silencio al inicio: detecta silence_start: 0 o casi 0
    start_match = re.search(r"silence_start:\s*0(?:\.0+)?\b.*?silence_end:\s*([\d.]+)", stderr, re.DOTALL)
    if start_match:
        val = float(start_match.group(1))
        # Solo recortar si el silencio es razonable (menos de max_start_trim)
        if 0.5 <= val <= max_start_trim:
            start_trim = val

    # Silencio al final: último silence_start detectado
    all_silence_starts = re.findall(r"silence_start:\s*([\d.]+)", stderr)
    if all_silence_starts:
        last_silence = float(all_silence_starts[-1])
        # Comprobar duración total
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", stderr)
        if dur_match:
            h, m, s = dur_match.groups()
            total_dur = int(h) * 3600 + int(m) * 60 + float(s)
            if (total_dur - last_silence) >= silence_dur and (total_dur - last_silence) <= 15.0:
                end_trim = last_silence

    return start_trim, end_trim


def extract_quick_audio(video_path: Path, output_audio: Path) -> Path:
    """Extrae rápidamente el audio en 16kHz mono sin alterar el video (para Whisper)."""
    ffmpeg_bin = find_binary("ffmpeg")
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_audio),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_audio


def remux_final_video(
    original_video: Path,
    cleaned_audio: Path,
    output_video: Path,
    srt_path: Path | None = None,
    start_trim: float = 0.0,
    end_trim: float | None = None,
    embed_subtitles: bool = True,
) -> None:
    """
    Combina el video original sin pérdida (-c:v copy) con el audio limpiado y la pista de subtítulos soft-sub.
    Aplica recorte de silencios si fue detectado y añade -movflags +faststart.
    """
    ffmpeg_bin = find_binary("ffmpeg")
    cmd = [ffmpeg_bin, "-y"]

    if start_trim > 0.0:
        cmd.extend(["-ss", str(start_trim)])
    if end_trim is not None:
        cmd.extend(["-to", str(end_trim)])

    cmd.extend(["-i", str(original_video)])

    # Si hubo recorte de tiempo en el video, el audio también debe recortarse con el mismo rango
    if start_trim > 0.0:
        cmd.extend(["-ss", str(start_trim)])
    if end_trim is not None:
        cmd.extend(["-to", str(end_trim)])
    cmd.extend(["-i", str(cleaned_audio)])

    if embed_subtitles and srt_path and srt_path.exists():
        cmd.extend(["-i", str(srt_path)])
        cmd.extend([
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-map", "2:s:0",
            "-c:v", "copy",
            "-c:a", "copy",
            "-c:s", "mov_text",
            "-metadata:s:s:0", "language=spa",
            "-metadata:s:s:0", "title=Español",
        ])
    else:
        cmd.extend([
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "copy",
        ])

    cmd.extend(["-movflags", "+faststart", str(output_video)])

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
