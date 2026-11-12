import os
import re
import sys
import shutil
import subprocess
import tomllib
from pathlib import Path
import click

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from obs_pipeline import __version__
from obs_pipeline.hardware import (
    is_windows,
    is_linux,
    get_safe_threads,
    find_binary,
    get_hw_video_encoder,
    send_notification,
)
from obs_pipeline.audio import process_audio
from obs_pipeline.video import detect_silence_trim, remux_final_video, extract_quick_audio
from obs_pipeline.subtitles import generate_subtitles
from obs_pipeline.metadata import generate_metadata, save_metadata_package
from obs_pipeline.thumbnail import create_thumbnails, check_gflow_auth
from obs_pipeline.security import run_sandboxed_gflow, get_gflow_jail_dir, PINNED_GFLOW_VERSION


def load_config(config_path: Path | None = None) -> dict:
    """Carga config.toml desde la ruta indicada o desde la raíz del proyecto."""
    if not config_path:
        config_path = Path(__file__).resolve().parent.parent.parent / "config.toml"
    if config_path.exists():
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    return {}


@click.group()
@click.version_option(__version__, prog_name="obs-pipe")
def main():
    """Pipeline multiplataforma de post-producción para OBS Studio."""
    pass


@main.command()
def doctor():
    """Diagnóstico del sistema, Antigravity CLI (agy) y blindaje de seguridad de gflow-cli."""
    click.echo(click.style(f"=== OBS Pipeline v{__version__} Doctor ===", fg="cyan", bold=True))

    os_name = "Windows" if is_windows() else ("Linux" if is_linux() else sys.platform)
    click.echo(f"  Sistema Operativo: {os_name}")

    safe_th = get_safe_threads()
    click.echo(f"  Hilos de CPU seguros para Whisper: {safe_th} (de {os.cpu_count()} totales)")

    # 1. FFmpeg
    ff = find_binary("ffmpeg")
    if shutil.which(ff) or Path(ff).exists():
        click.echo(click.style(f"  [OK] FFmpeg detectado: {ff}", fg="green"))
    else:
        click.echo(click.style("  [FALLO] FFmpeg no encontrado en PATH", fg="red"))

    # 2. Hardware Encoder
    enc, enc_args = get_hw_video_encoder()
    click.echo(f"  Codificador de video HW: {enc} ({' '.join(enc_args)})")

    # 3. Antigravity CLI (agy)
    agy_bin = find_binary("agy")
    if shutil.which(agy_bin) or Path(agy_bin).exists():
        try:
            ver = subprocess.run([agy_bin, "--version"], capture_output=True, text=True, check=False).stdout.strip()
        except Exception:
            ver = "detectado"
        click.echo(click.style(f"  [OK] Antigravity CLI (agy v{ver}): {agy_bin}", fg="green"))
    else:
        click.echo(click.style("  [AVISO] Antigravity CLI (agy) no detectado (se usará analizador semántico offline)", fg="yellow"))

    # 4. gflow-cli + Blindaje de Seguridad
    gflow_bin = find_binary("gflow")
    jail_dir = get_gflow_jail_dir()
    click.echo(click.style(f"  [BLINDAJE] Jaula aislada para gflow-cli (v{PINNED_GFLOW_VERSION} pinned): {jail_dir}", fg="cyan"))
    if is_linux() and shutil.which("bwrap"):
        click.echo(click.style("  [BLINDAJE] Bubblewrap (bwrap) activo para aislamiento de kernel en Linux", fg="green"))
    else:
        click.echo(click.style("  [BLINDAJE] Redirección de perfil (APPDATA/USERPROFILE) + Telemetría OFF activa", fg="green"))

    if shutil.which(gflow_bin) or Path(gflow_bin).exists():
        auth_ok = check_gflow_auth()
        status_msg = "Sesión Activa en Jaula" if auth_ok else "Sin sesión en jaula (ejecuta: uv run obs-pipe gflow-login)"
        fg_col = "green" if auth_ok else "yellow"
        click.echo(click.style(f"  [{'OK' if auth_ok else 'AVISO'}] gflow-cli: {status_msg}", fg=fg_col))
    else:
        click.echo(click.style("  [AVISO] gflow-cli no instalado en PATH", fg="yellow"))

    click.echo(click.style("\nDiagnóstico completado.", fg="cyan"))


@main.command("gflow-login")
def gflow_login():
    """Inicia sesión en Google Flow dentro de la jaula aislada (sin tocar tu navegador principal)."""
    jail_dir = get_gflow_jail_dir()
    click.echo(click.style("🛡️ Iniciando sesión de Google Flow dentro de la jaula de seguridad...", fg="cyan", bold=True))
    click.echo(f"   Perfil aislado en: {jail_dir}")
    click.echo("   Tus navegadores personales y credenciales del sistema están ocultos para gflow-cli.\n")
    run_sandboxed_gflow(["auth", "login", "--browser", "chrome"], timeout=300, interactive=True)


def _run_publish_flow(video_path: Path, target_dir: Path, lang: str | None = None) -> None:
    """Flujo de publicación para videos ya editados: transcripción + metadatos agy + 3 miniaturas."""
    cfg = load_config()
    video_stem = video_path.stem

    click.echo(click.style(f"\n🎬 Iniciando pipeline de publicación (Modo B - Video Editado): {video_path.name}", fg="cyan", bold=True))
    click.echo(f"📂 Carpeta de entrega: {target_dir}")

    # 1. Extracción rápida de audio de referencia para Whisper (sin alterar video)
    click.echo("\n[1/4] 🎙️ Extrayendo pista de audio de referencia para Whisper (sin alterar el video editado)...")
    ref_audio = target_dir / "audio_referencia.wav"
    extract_quick_audio(video_path, ref_audio)
    click.echo(click.style("  [OK] Pista 16kHz mono extraída para análisis acústico", fg="green"))

    # 2. Subtítulos con faster-whisper int8
    click.echo("\n[2/4] 📝 Generando subtítulos con faster-whisper (CPU int8)...")
    sub_cfg = cfg.get("subtitles", {})
    language = lang or cfg.get("general", {}).get("language", "es")
    threads = get_safe_threads(cfg.get("general", {}).get("safe_cpu_threads", 0))
    sub_data = generate_subtitles(ref_audio, target_dir, sub_cfg, language=language, cpu_threads=threads)
    click.echo(click.style(f"  [OK] Subtítulos exportados: .srt, .vtt y .txt ({len(sub_data['segments'])} fragmentos)", fg="green"))

    # 3. Metadatos SEO y Capítulos exactos con Antigravity CLI (agy)
    click.echo("\n[3/4] 🧠 Analizando transcripción y generando títulos SEO, capítulos exactos y prompt de miniatura...")
    thumb_cfg = cfg.get("thumbnail", {})
    template = thumb_cfg.get("prompt_template", "")
    meta = generate_metadata(
        video_stem,
        sub_data["segments"],
        sub_data["full_text"],
        template,
        transcript_txt_path=sub_data["txt_path"],
    )
    meta_doc = save_metadata_package(target_dir, meta)
    click.echo(click.style(f"  [OK] Paquete guardado en: {meta_doc.name} (motor: {meta.get('source')})", fg="green"))

    # 4. Set global de 3 variantes de miniatura
    click.echo("\n[4/4] 🎨 Diseñando miniaturas (3 variantes: Widgets IA, Personaje IA, Local con fotograma real)...")
    thumbs = create_thumbnails(video_path, target_dir, meta, thumb_cfg)
    for k, p in thumbs.items():
        click.echo(click.style(f"  [OK] Miniatura ({k}): {p.name}", fg="green"))

    send_notification("OBS Pipeline", f"Video editado {video_path.name} procesado y listo.")
    click.echo(click.style("\n✨ ¡Proceso completado con éxito! Todo el material está listo para publicar en YouTube.\n", fg="green", bold=True))


@main.command()
@click.argument("video_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "-o", type=click.Path(path_type=Path), default=None, help="Directorio de salida.")
@click.option("--lang", "-l", default=None, help="Idioma de transcripción (ej: es, en).")
def publish(video_path: Path, out: Path | None, lang: str | None):
    """Modo B: Procesa un video ya editado (transcripción + metadatos agy + 3 miniaturas sin re-editar)."""
    cfg = load_config()
    video_stem = video_path.stem
    if out:
        target_dir = out
    elif cfg.get("general", {}).get("output_dir"):
        target_dir = Path(cfg["general"]["output_dir"]) / f"post_{video_stem}"
    else:
        target_dir = video_path.parent / f"post_{video_stem}"

    target_dir.mkdir(parents=True, exist_ok=True)
    _run_publish_flow(video_path, target_dir, lang=lang)


@main.command()
@click.argument("video_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--mode", "-m", type=click.Choice(["raw", "edited"], case_sensitive=False), default="raw", help="Modo: 'raw' (grabación cruda OBS) o 'edited' (video ya editado).")
@click.option("--jump-cuts/--no-jump-cuts", default=None, help="Activar eliminación de pausas internas mayores a 1s en modo raw.")
@click.option("--out", "-o", type=click.Path(path_type=Path), default=None, help="Directorio de salida.")
@click.option("--lang", "-l", default=None, help="Idioma de transcripción (ej: es, en).")
def process(video_path: Path, mode: str, jump_cuts: bool | None, out: Path | None, lang: str | None):
    """Procesa una grabación de OBS: audio estudio + subtítulos + video master + metadatos (agy) + miniaturas."""
    cfg = load_config()
    video_stem = video_path.stem

    if out:
        target_dir = out
    elif cfg.get("general", {}).get("output_dir"):
        target_dir = Path(cfg["general"]["output_dir"]) / f"post_{video_stem}"
    else:
        target_dir = video_path.parent / f"post_{video_stem}"

    target_dir.mkdir(parents=True, exist_ok=True)

    if mode.lower() == "edited":
        _run_publish_flow(video_path, target_dir, lang=lang)
        return

    # Modo A: Grabación Cruda de OBS
    click.echo(click.style(f"\n🎬 Iniciando pipeline (Modo A - Grabación Cruda OBS): {video_path.name}", fg="cyan", bold=True))
    click.echo(f"📂 Carpeta de entrega: {target_dir}")

    # 1. Audio DSP Cleanup
    click.echo("\n[1/5] 🔊 Limpiando audio (canales L/R, afftdn, highpass, loudnorm)...")
    cleaned_audio = target_dir / "audio_estudio.aac"
    audio_cfg = cfg.get("audio", {})
    ch_fix, _ = process_audio(video_path, cleaned_audio, audio_cfg)
    if ch_fix:
        click.echo(click.style(f"  -> Corrección aplicada: Canal mudo detectado ({ch_fix})", fg="yellow"))
    click.echo(click.style("  [OK] Audio masterizado en 192k AAC EBU R128 (-16 LUFS)", fg="green"))

    # 2. Subtítulos con faster-whisper int8
    click.echo("\n[2/5] 📝 Generando subtítulos con faster-whisper (CPU int8)...")
    sub_cfg = cfg.get("subtitles", {})
    language = lang or cfg.get("general", {}).get("language", "es")
    threads = get_safe_threads(cfg.get("general", {}).get("safe_cpu_threads", 0))
    sub_data = generate_subtitles(cleaned_audio, target_dir, sub_cfg, language=language, cpu_threads=threads)
    click.echo(click.style(f"  [OK] Subtítulos exportados: .srt, .vtt y .txt ({len(sub_data['segments'])} fragmentos)", fg="green"))

    # 3. Remuxing de video (cero pérdida) + incrustación de subtítulos
    click.echo("\n[3/5] ✂️ Ensamblando video masterizado (Stream copy + soft-subs)...")
    vid_cfg = cfg.get("video", {})
    start_trim = 0.0
    end_trim = None
    if vid_cfg.get("auto_trim_silence", True):
        # Detección precisa de silencio post-DSP sobre el audio limpio (piso de ruido < -55dB)
        s_db = float(vid_cfg.get("trim_silence_db", -45.0))
        s_dur = float(vid_cfg.get("trim_silence_duration", 0.8))
        start_trim, end_trim = detect_silence_trim(cleaned_audio, silence_db=s_db, silence_dur=s_dur)
        if start_trim > 0.0 or end_trim is not None:
            click.echo(f"  -> Recorte de silencio aplicado (post-DSP): inicio={start_trim:.2f}s, fin={end_trim}")

    final_video = target_dir / f"{video_stem}_masterizado.mp4"
    remux_final_video(
        video_path,
        cleaned_audio,
        final_video,
        srt_path=sub_data["srt_path"],
        start_trim=start_trim,
        end_trim=end_trim,
        embed_subtitles=vid_cfg.get("embed_subtitles", True),
    )
    click.echo(click.style(f"  [OK] Video masterizado listo: {final_video.name}", fg="green"))

    # 4. Generación de Metadatos y Títulos SEO con Antigravity CLI (agy) + respaldo semántico
    click.echo("\n[4/5] 🧠 Analizando transcripción y generando títulos, capítulos y prompt de miniatura...")
    thumb_cfg = cfg.get("thumbnail", {})
    template = thumb_cfg.get("prompt_template", "")
    meta = generate_metadata(
        video_stem,
        sub_data["segments"],
        sub_data["full_text"],
        template,
        transcript_txt_path=sub_data["txt_path"],
    )
    meta_doc = save_metadata_package(target_dir, meta)
    click.echo(click.style(f"  [OK] Paquete guardado en: {meta_doc.name} (motor: {meta.get('source')})", fg="green"))

    # 5. Miniaturas (Google Flow en jaula / Local mejorada)
    click.echo("\n[5/5] 🎨 Diseñando miniaturas...")
    thumbs = create_thumbnails(video_path, target_dir, meta, thumb_cfg)
    for k, p in thumbs.items():
        click.echo(click.style(f"  [OK] Miniatura ({k}): {p.name}", fg="green"))

    send_notification("OBS Pipeline", f"Video {video_path.name} procesado y listo.")
    click.echo(click.style("\n✨ ¡Proceso completado con éxito! Todo el material está listo para publicar.\n", fg="green", bold=True))


@main.command()
@click.argument("video_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--dir", "-d", "target_dir", type=click.Path(exists=True, file_okay=False, path_type=Path), required=True)
def refresh_meta(video_path: Path, target_dir: Path):
    """Regenera títulos, capítulos, prompt y miniatura a partir de una transcripción ya existente."""
    cfg = load_config()
    txt_path = target_dir / "transcripcion.txt"
    if not txt_path.exists():
        click.echo(click.style("Error: No existe transcripcion.txt en la carpeta indicada.", fg="red"))
        sys.exit(1)

    raw_lines = txt_path.read_text(encoding="utf-8").splitlines()
    segments = []
    full_parts = []
    for line in raw_lines:
        m = re.match(r"^\[(\d+):(\d+)\]\s*(.+)$", line.strip())
        if m:
            mins, secs, txt = int(m.group(1)), int(m.group(2)), m.group(3)
            segments.append({"start": mins * 60 + secs, "end": mins * 60 + secs + 5, "text": txt})
            full_parts.append(txt)

    thumb_cfg = cfg.get("thumbnail", {})
    template = thumb_cfg.get("prompt_template", "")
    click.echo(click.style("🧠 Re-analizando transcripción completa...", fg="cyan"))
    meta = generate_metadata(
        video_path.stem,
        segments,
        " ".join(full_parts),
        template,
        transcript_txt_path=txt_path,
    )
    meta_doc = save_metadata_package(target_dir, meta)
    click.echo(click.style(f"  [OK] {meta_doc.name} actualizado (motor: {meta.get('source')})", fg="green"))

    thumbs = create_thumbnails(video_path, target_dir, meta, thumb_cfg)
    for k, p in thumbs.items():
        click.echo(click.style(f"  [OK] Miniatura actualizada ({k}): {p.name}", fg="green"))


@main.command()
@click.option("--dir", "-d", "watch_dir", type=click.Path(path_type=Path), default=None, help="Carpeta a vigilar.")
def watch(watch_dir: Path | None):
    """Vigila la carpeta de grabaciones de OBS y procesa automáticamente al terminar cada video."""
    cfg = load_config()
    if not watch_dir:
        configured_dir = cfg.get("paths", {}).get("obs_recordings_dir")
        if configured_dir:
            watch_dir = Path(configured_dir).expanduser()
        elif is_windows():
            watch_dir = Path.home() / "Downloads"
        else:
            desc = Path.home() / "Descargas"
            watch_dir = desc if desc.exists() else (Path.home() / "Downloads")

    if not watch_dir.exists():
        click.echo(click.style(f"Error: La carpeta {watch_dir} no existe.", fg="red"))
        sys.exit(1)

    from obs_pipeline.watcher import start_watching

    click.echo(click.style(f"👀 Vigilando carpeta de OBS: {watch_dir}", fg="cyan", bold=True))
    click.echo("Graba en OBS con tranquilidad. Al pulsar 'Detener grabación', este script procesará el video automáticamente.")
    click.echo("Presiona Ctrl+C para detener el vigilante.\n")

    def _on_new_video(p: Path):
        try:
            from click.testing import CliRunner
            runner = CliRunner()
            runner.invoke(process, [str(p)])
        except Exception as e:
            click.echo(f"Error procesando {p.name}: {e}")

    start_watching(watch_dir, _on_new_video)
