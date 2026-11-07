import re
import subprocess
from pathlib import Path
from obs_pipeline.hardware import find_binary


def check_channel_balance(video_path: Path, max_check_seconds: int = 30, diff_threshold: float = 20.0) -> str | None:
    """
    Analiza los primeros 30 segundos del video para comprobar si uno de los canales quedó mudo.
    Retorna el filtro pan correctivo o None si el audio ya es balanceado.
    """
    ffmpeg_bin = find_binary("ffmpeg")
    cmd = [
        ffmpeg_bin,
        "-t", str(max_check_seconds),
        "-i", str(video_path),
        "-af", "astats",
        "-f", "null",
        "-"
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        stderr = proc.stderr
    except subprocess.CalledProcessError as e:
        stderr = e.stderr

    # Parsear RMS level dB por canal
    # Channel 1: ... RMS level dB: -24.5
    # Channel 2: ... RMS level dB: -80.0
    c1_rms = None
    c2_rms = None

    c1_match = re.search(r"Channel:\s*1\b.*?RMS level dB:\s*(-?[\d.]+)", stderr, re.DOTALL)
    c2_match = re.search(r"Channel:\s*2\b.*?RMS level dB:\s*(-?[\d.]+)", stderr, re.DOTALL)

    if c1_match:
        try:
            c1_rms = float(c1_match.group(1))
        except ValueError:
            pass
    if c2_match:
        try:
            c2_rms = float(c2_match.group(1))
        except ValueError:
            pass

    if c1_rms is not None and c2_rms is not None:
        # Si canal derecho está mudo (muy bajo respecto al izquierdo)
        if (c1_rms - c2_rms) >= diff_threshold:
            return "pan=stereo|c0=c0|c1=c0"
        # Si canal izquierdo está mudo respecto al derecho
        elif (c2_rms - c1_rms) >= diff_threshold:
            return "pan=stereo|c0=c1|c1=c1"

    return None


def build_audio_filter_chain(audio_cfg: dict, channel_fix: str | None = None) -> str:
    """Construye la cadena completa de filtros DSP de estudio."""
    filters = []

    # 1. Corrección estéreo / mono si fue necesaria
    if channel_fix:
        filters.append(channel_fix)

    # 2. Paso alto para cortar retumbos y zumbidos (< 80 Hz)
    highpass = audio_cfg.get("highpass_freq", 80)
    filters.append(f"highpass=f={highpass}")

    # 3. Quitar chasquidos impulsivos (teclado/micro)
    filters.append("adeclick")

    # 4. Reducción de ruido espectral adaptativo
    nr = audio_cfg.get("denoise_nr", 14)
    nf = audio_cfg.get("denoise_nf", -25)
    filters.append(f"afftdn=nr={nr}:nf={nf}:tn=1")

    # 5. Compresión suave de rango dinámico
    filters.append("acompressor=threshold=-18dB:ratio=2.5:attack=10:release=100")

    # 6. Normalización EBU R128 para nivel estándar de podcast/YouTube
    lufs = audio_cfg.get("target_loudness_lufs", -16.0)
    tp = audio_cfg.get("target_true_peak", -1.5)
    filters.append(f"loudnorm=I={lufs}:TP={tp}:LRA=11")

    return ",".join(filters)


def process_audio(input_path: Path, output_audio_path: Path, audio_cfg: dict) -> tuple[str | None, str]:
    """
    Procesa y limpia el audio del video de entrada y lo exporta como AAC/WAV para transcripción y remux.
    Retorna (channel_fix_applied, filter_chain_used).
    """
    channel_fix = None
    if audio_cfg.get("auto_fix_channels", True):
        thresh = float(audio_cfg.get("channel_db_diff_threshold", 20.0))
        channel_fix = check_channel_balance(input_path, diff_threshold=thresh)

    filter_chain = build_audio_filter_chain(audio_cfg, channel_fix)
    ffmpeg_bin = find_binary("ffmpeg")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", str(input_path),
        "-vn",
        "-af", filter_chain,
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        str(output_audio_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return channel_fix, filter_chain
