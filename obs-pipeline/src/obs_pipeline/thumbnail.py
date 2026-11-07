import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from obs_pipeline.hardware import find_binary
from obs_pipeline.security import run_sandboxed_gflow, get_gflow_jail_dir


def check_gflow_auth() -> bool:
    """Verifica si gflow-cli tiene sesión activa dentro de su jaula de seguridad."""
    try:
        res = run_sandboxed_gflow(["auth", "status"], timeout=20)
        return res.returncode == 0
    except Exception:
        return False


def generate_flow_thumbnail(
    prompt: str,
    output_image_path: Path,
    model: str = "nano2",
) -> bool:
    """
    Invoca gflow-cli dentro de la jaula de seguridad (security.py) para generar
    la miniatura 16:9 con Nano Banana 2.1 en Google Flow sin gastar créditos de video.
    """
    args = [
        "image",
        "t2i",
        prompt,
        "--model",
        model,
        "--aspect",
        "16:9",
        "-o",
        str(output_image_path),
    ]
    try:
        res = run_sandboxed_gflow(args, output_dir=output_image_path.parent, timeout=120)
        return res.returncode == 0 and output_image_path.exists()
    except Exception:
        return False


def get_video_duration(video_path: Path) -> float:
    """Obtiene la duración total del video en segundos."""
    ffmpeg_bin = find_binary("ffmpeg")
    try:
        proc = subprocess.run([ffmpeg_bin, "-i", str(video_path)], capture_output=True, text=True, check=False)
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", proc.stderr)
        if m:
            h, mins, s = m.groups()
            return int(h) * 3600 + int(mins) * 60 + float(s)
    except Exception:
        pass
    return 120.0


def extract_video_frame(video_path: Path, output_frame_path: Path, timestamp_sec: float | None = None) -> bool:
    """Extrae un fotograma representativo del cuerpo del video (35% de la duración)."""
    if timestamp_sec is None:
        dur = get_video_duration(video_path)
        timestamp_sec = max(10.0, dur * 0.35)

    ffmpeg_bin = find_binary("ffmpeg")
    cmd = [
        ffmpeg_bin,
        "-y",
        "-ss",
        f"{timestamp_sec:.2f}",
        "-i",
        str(video_path),
        "-vframes",
        "1",
        "-q:v",
        "2",
        str(output_frame_path),
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return output_frame_path.exists()
    except Exception:
        return False


def _draw_gradient_headline(base_img: Image.Image, text: str, x: int, y: int, font: ImageFont.FreeTypeFont) -> int:
    """Dibuja texto grande con degradado vertical amarillo-naranja (#FFE600 -> #FF5500) y contorno grueso."""
    draw = ImageDraw.Draw(base_img)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = max(1, bbox[2] - bbox[0])
    th = max(1, bbox[3] - bbox[1] + 20)

    # Contorno grueso exterior
    for ox in range(-8, 9, 2):
        for oy in range(-8, 9, 2):
            if ox * ox + oy * oy <= 64:
                draw.text((x + ox, y + oy), text, font=font, fill=(25, 10, 5, 255))

    mask = Image.new("L", (tw + 20, th + 20), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((10 - bbox[0], 10 - bbox[1]), text, font=font, fill=255)

    grad = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad)
    for row in range(th + 20):
        t = row / max(1, th + 19)
        r = 255
        g = int(230 * (1 - t) + 95 * t)
        b = int(10 * (1 - t))
        grad_draw.line([(0, row), (tw + 20, row)], fill=(r, g, b, 255))

    base_img.paste(grad, (x - 10 + bbox[0], y - 10 + bbox[1]), mask)
    return th


def generate_local_thumbnail(
    video_path: Path,
    output_image_path: Path,
    headline: str,
    subtitle: str,
) -> Path:
    """
    Genera localmente una miniatura 1280x720 de respaldo con fondo azul medianoche (#091020),
    trazos neón, captura del 35% del video y tipografía en degradado.
    """
    width, height = 1280, 720
    img = Image.new("RGBA", (width, height), (9, 16, 32, 255))
    draw = ImageDraw.Draw(img)

    neon_lines = [
        ([(0, 90), (220, 0)], (0, 150, 255, 210), 7),
        ([(160, 70), (260, 0)], (255, 130, 0, 190), 4),
        ([(680, 120), (830, 0)], (0, 210, 255, 180), 5),
        ([(1060, 140), (1240, 0)], (255, 140, 0, 200), 6),
        ([(350, height), (500, height - 130)], (0, 160, 255, 190), 5),
        ([(510, height), (660, height - 130)], (255, 130, 0, 210), 6),
        ([(1050, height), (width, height - 180)], (0, 210, 255, 210), 7),
    ]
    for coords, color, w in neon_lines:
        draw.line(coords, fill=color, width=w)

    temp_frame = output_image_path.parent / "temp_frame.png"
    if extract_video_frame(video_path, temp_frame):
        try:
            vf = Image.open(temp_frame).convert("RGBA")
            vf_w, vf_h = 560, 380
            vf = vf.resize((vf_w, vf_h), Image.Resampling.LANCZOS)

            pos_x = width - vf_w - 48
            pos_y = (height - vf_h) // 2
            for pad, alpha in [(10, 50), (6, 110), (3, 240)]:
                draw.rounded_rectangle(
                    [pos_x - pad, pos_y - pad, pos_x + vf_w + pad, pos_y + vf_h + pad],
                    radius=14,
                    outline=(0, 210, 255, alpha),
                    width=3,
                )
            img.paste(vf, (pos_x, pos_y))
        except Exception:
            pass
        finally:
            if temp_frame.exists():
                temp_frame.unlink(missing_ok=True)

    font_bold = None
    font_banner = None
    headline_clean = headline.strip().upper()[:11]
    headline_size = 118 if len(headline_clean) <= 7 else 92

    for font_name in ["impact.ttf", "arialbd.ttf", "CascadiaCode-Bold.otf", "DejaVuSans-Bold.ttf"]:
        try:
            font_bold = ImageFont.truetype(font_name, headline_size)
            font_banner = ImageFont.truetype(font_name, 52)
            break
        except Exception:
            continue
    if font_bold is None:
        font_bold = ImageFont.load_default()
        font_banner = ImageFont.load_default()

    text_x = 64
    text_y = 195
    th = _draw_gradient_headline(img, headline_clean, text_x, text_y, font_bold)

    banner_text = subtitle.strip().upper()[:18]
    tb = draw.textbbox((0, 0), banner_text, font=font_banner)
    bw = max(440, (tb[2] - tb[0]) + 80)
    bh = 94
    banner_y = text_y + th + 22

    draw.rounded_rectangle(
        [text_x, banner_y, text_x + bw, banner_y + bh],
        radius=36,
        fill=(0, 116, 232, 255),
        outline=(60, 180, 255, 255),
        width=3,
    )
    tx = text_x + (bw - (tb[2] - tb[0])) // 2
    ty = banner_y + (bh - (tb[3] - tb[1])) // 2 - tb[1]
    draw.text((tx, ty), banner_text, font=font_banner, fill=(255, 255, 255, 255))

    img.convert("RGB").save(str(output_image_path), quality=95)
    return output_image_path


def create_thumbnails(
    video_path: Path,
    output_dir: Path,
    meta: dict,
    thumb_cfg: dict,
) -> dict:
    """
    Genera el set global de 3 variantes de miniaturas para tener siempre de dónde elegir:
    1. miniatura_1_elementos.png: IA con widgets/elementos gráficos de las herramientas del video.
    2. miniatura_2_personaje.png: IA con desarrollador cel-shaded anime en la acción del video.
    3. miniatura_3_local.png: Diagramación gráfica local con fotograma real del video.
    """
    results = {}
    headline = meta.get("headline", "WINDOWS")
    subtitle = meta.get("subtitle", "3 APPS PRO")
    tech_info = meta.get("tech_info", {})
    tecnologia = tech_info.get("tech", "Software Tutorial")
    icon = tech_info.get("icon", "modern glowing tech emblem")
    model = thumb_cfg.get("gflow_model", "nano2")

    # 1. Prompt Variante 1 (Elementos temáticos / herramientas)
    subject_tools = tech_info.get("subject", "three floating glowing holographic tech icons")
    prompt_tools = (
        f"2D flat vector YouTube thumbnail, 16:9 aspect ratio. {tecnologia} tutorial theme. "
        f"On the left side, bold large headline text reading \"{headline}\" with vibrant orange-yellow gradient fill and thick outline, "
        f"directly above \"{subtitle}\" in crisp white text inside a clean electric blue pill banner. "
        f"Absolutely no extra badges, no secondary stickers. "
        f"On the right side, {subject_tools}. "
        f"Behind it, a single clean glowing {icon}. "
        f"Deep midnight blue background, clean composition, high contrast, vibrant electric blue and bright orange neon accents, "
        f"bold outlines, minimal visual clutter, sharp graphic design."
    )

    # 2. Prompt Variante 2 (Desarrollador anime cel-shaded)
    prompt_character = (
        f"2D flat vector YouTube thumbnail, 16:9 aspect ratio. {tecnologia} tutorial theme. "
        f"On the left side, bold large headline text reading \"{headline}\" with vibrant orange-yellow gradient fill and thick outline, "
        f"directly above \"{subtitle}\" in crisp white text inside a clean electric blue pill banner. "
        f"Absolutely no extra badges, no secondary stickers. "
        f"On the right side, a 2D cel-shaded anime developer typing on a laptop with glowing code terminal and floating neon tool widgets. "
        f"Behind him, a single clean glowing {icon}. "
        f"Deep midnight blue background, clean composition, high contrast, vibrant electric blue and bright orange neon accents, "
        f"bold outlines, minimal visual clutter, sharp graphic design."
    )

    # Guardar ambos prompts para inspección
    (output_dir / "prompt_miniatura_v1_elementos.txt").write_text(prompt_tools, encoding="utf-8")
    (output_dir / "prompt_miniatura_v2_personaje.txt").write_text(prompt_character, encoding="utf-8")

    # Intentar generar variantes IA si hay sesión activa en gflow
    if thumb_cfg.get("provider", "gflow") == "gflow" and check_gflow_auth():
        p1 = output_dir / "miniatura_1_elementos.png"
        if generate_flow_thumbnail(prompt_tools, p1, model=model):
            results["ia_elementos"] = p1

        p2 = output_dir / "miniatura_2_personaje.png"
        if generate_flow_thumbnail(prompt_character, p2, model=model):
            results["ia_personaje"] = p2

    # Variante 3 (Siempre garantizada): Miniatura local con fotograma real
    local_path = output_dir / "miniatura_3_local.png"
    generate_local_thumbnail(video_path, local_path, headline, subtitle)
    results["local_fotograma"] = local_path

    return results
