import re
import shutil
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


def _get_system_fonts(headline_size: int, sub_size: int) -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    """Carga fuentes truetype robustas con soporte multiplataforma (Windows y Linux)."""
    font_candidates = [
        "impact.ttf",
        "arialbd.ttf",
        "CascadiaCode-Bold.otf",
        "CascadiaCode.ttf",
        "DejaVuSans-Bold.ttf",
        "LiberationSans-Bold.ttf",
        "Ubuntu-B.ttf",
    ]
    for fn in font_candidates:
        try:
            fb = ImageFont.truetype(fn, headline_size)
            fs = ImageFont.truetype(fn, sub_size)
            return fb, fs
        except Exception:
            continue
    return ImageFont.load_default(), ImageFont.load_default()


def composite_sharp_typography(
    base_image: Path | Image.Image,
    output_path: Path,
    headline: str,
    subtitle: str,
    width: int = 1920,
    height: int = 1080,
    supersample: int = 2,
    clean_left_vignette: bool = True,
) -> Path:
    """
    Motor tipográfico híbrido con supersampling 2x (3840x2160) y filtrado Lanczos:
    Elimina artefactos borrosos o pixelados de las IAs generando textos vectoriales de máxima nitidez:
    - Titular en degradado vertical amarillo-naranja (#FFE600 -> #FF4D00) con contorno oscuro y sombra suave.
    - Pastilla azul eléctrico (#0074E8 con borde cian #38B6FF) con esquinas redondeadas matemáticas.
    - Exportación nativa a 1920x1080 Full HD (< 2 MB) lista para YouTube.
    """
    if isinstance(base_image, Path):
        base = Image.open(base_image).convert("RGBA")
    else:
        base = base_image.convert("RGBA")

    # 1. Base escalada a 1920x1080 con Lanczos de alta precisión
    base_1080 = base.resize((width, height), Image.Resampling.LANCZOS)

    # 2. Lienzo 2X de supersampling
    w_2x = width * supersample
    h_2x = height * supersample
    overlay_2x = Image.new("RGBA", (w_2x, h_2x), (0, 0, 0, 0))

    # 3. Fundido sutil en el tercio izquierdo para eliminar texto borroso previo de la IA
    if clean_left_vignette:
        plate = Image.new("RGBA", (w_2x, h_2x), (0, 0, 0, 0))
        p_draw = ImageDraw.Draw(plate)
        fade_limit = int(w_2x * 0.46)
        fade_start = int(w_2x * 0.26)
        for x in range(fade_limit):
            if x < fade_start:
                alpha = 245
            else:
                t = (x - fade_start) / float(fade_limit - fade_start)
                alpha = int(245 * (1.0 - t * t))
            p_draw.line([(x, 0), (x, h_2x)], fill=(9, 16, 32, alpha))
        overlay_2x = Image.alpha_composite(overlay_2x, plate)

    draw = ImageDraw.Draw(overlay_2x)

    headline_clean = headline.strip().upper()[:12]
    # Escala de fuente dinámica según la longitud
    base_font_size = 250 if len(headline_clean) <= 7 else (210 if len(headline_clean) <= 9 else 180)
    font_bold, font_sub = _get_system_fonts(base_font_size, 115)

    bbox_h = draw.textbbox((0, 0), headline_clean, font=font_bold)
    hw = bbox_h[2] - bbox_h[0]
    hh = bbox_h[3] - bbox_h[1]

    text_x = int(w_2x * 0.05)  # Margen izquierdo profesional (~190px en 2x)
    text_y = int(h_2x * 0.28)

    # 4. Contorno oscuro exterior (30px en 2x = 15px en 1080p) con sombra suave
    stroke_layer = Image.new("RGBA", (w_2x, h_2x), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(stroke_layer)
    stroke_r = 28
    for ox in range(-stroke_r, stroke_r + 1, 3):
        for oy in range(-stroke_r, stroke_r + 1, 3):
            if ox * ox + oy * oy <= stroke_r * stroke_r:
                s_draw.text((text_x + ox, text_y + oy), headline_clean, font=font_bold, fill=(8, 12, 20, 255))

    # Sombra difusa debajo del contorno
    from PIL import ImageFilter
    stroke_shadow = stroke_layer.filter(ImageFilter.GaussianBlur(radius=8))
    overlay_2x = Image.alpha_composite(overlay_2x, stroke_shadow)
    overlay_2x = Image.alpha_composite(overlay_2x, stroke_layer)

    # 5. Relleno en degradado vertical amarillo-naranja
    mask = Image.new("L", (hw + 60, hh + 60), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.text((30 - bbox_h[0], 30 - bbox_h[1]), headline_clean, font=font_bold, fill=255)

    grad = Image.new("RGBA", (hw + 60, hh + 60), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grad)
    for r in range(hh + 60):
        t = r / max(1, hh + 59)
        red = 255
        green = int(230 * (1 - t) + 77 * t)
        blue = int(10 * (1 - t))
        g_draw.line([(0, r), (hw + 60, r)], fill=(red, green, blue, 255))

    grad_text = Image.new("RGBA", (w_2x, h_2x), (0, 0, 0, 0))
    grad_text.paste(grad, (text_x - 30 + bbox_h[0], text_y - 30 + bbox_h[1]), mask)
    overlay_2x = Image.alpha_composite(overlay_2x, grad_text)

    # 6. Pastilla azul eléctrico para el subtítulo
    sub_clean = subtitle.strip().upper()[:20]
    tb = draw.textbbox((0, 0), sub_clean, font=font_sub)
    sw = tb[2] - tb[0]
    sh = tb[3] - tb[1]

    pill_w = max(860, sw + 160)
    pill_h = 200
    pill_y = text_y + hh + 75
    pill_radius = 80

    pill_layer = Image.new("RGBA", (w_2x, h_2x), (0, 0, 0, 0))
    pill_draw = ImageDraw.Draw(pill_layer)

    # Sombra arrojada de la pastilla
    pill_draw.rounded_rectangle(
        [text_x + 8, pill_y + 14, text_x + pill_w + 8, pill_y + pill_h + 14],
        radius=pill_radius,
        fill=(0, 0, 0, 160),
    )
    # Cuerpo principal (#0074E8) con borde cian neón (#38B6FF)
    pill_draw.rounded_rectangle(
        [text_x, pill_y, text_x + pill_w, pill_y + pill_h],
        radius=pill_radius,
        fill=(0, 116, 232, 255),
        outline=(56, 182, 255, 255),
        width=8,
    )

    # Texto blanco nítido centrado
    stx = text_x + (pill_w - sw) // 2
    sty = pill_y + (pill_h - sh) // 2 - tb[1]
    pill_draw.text((stx, sty), sub_clean, font=font_sub, fill=(255, 255, 255, 255))

    overlay_2x = Image.alpha_composite(overlay_2x, pill_layer)

    # 7. Reducción con Lanczos a 1920x1080 (antialiasing perfecto subpixel)
    overlay_1080 = overlay_2x.resize((width, height), Image.Resampling.LANCZOS)
    final_img = Image.alpha_composite(base_1080, overlay_1080)
    final_rgb = final_img.convert("RGB")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".png":
        final_rgb.save(str(output_path), "PNG", optimize=True)
    else:
        final_rgb.save(str(output_path), "JPEG", quality=98)

    return output_path


def generate_local_thumbnail(
    video_path: Path,
    output_image_path: Path,
    headline: str,
    subtitle: str,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """
    Genera localmente una miniatura nativa 1920x1080 Full HD con fondo azul medianoche (#091020),
    trazos neón de alta definición, captura del 35% del video y tipografía vectorial nítida.
    """
    img = Image.new("RGBA", (width, height), (9, 16, 32, 255))
    draw = ImageDraw.Draw(img)

    neon_lines = [
        ([(0, 135), (330, 0)], (0, 150, 255, 210), 10),
        ([(240, 105), (390, 0)], (255, 130, 0, 190), 6),
        ([(1020, 180), (1245, 0)], (0, 210, 255, 180), 7),
        ([(1590, 210), (1860, 0)], (255, 140, 0, 200), 9),
        ([(525, height), (750, height - 195)], (0, 160, 255, 190), 7),
        ([(765, height), (990, height - 195)], (255, 130, 0, 210), 9),
        ([(1575, height), (width, height - 270)], (0, 210, 255, 210), 10),
    ]
    for coords, color, w in neon_lines:
        draw.line(coords, fill=color, width=w)

    temp_frame = output_image_path.parent / "temp_frame_1080.png"
    if extract_video_frame(video_path, temp_frame):
        try:
            vf = Image.open(temp_frame).convert("RGBA")
            vf_w, vf_h = 860, 560
            vf = vf.resize((vf_w, vf_h), Image.Resampling.LANCZOS)

            pos_x = width - vf_w - 70
            pos_y = (height - vf_h) // 2
            for pad, alpha in [(14, 50), (9, 110), (4, 240)]:
                draw.rounded_rectangle(
                    [pos_x - pad, pos_y - pad, pos_x + vf_w + pad, pos_y + vf_h + pad],
                    radius=20,
                    outline=(0, 210, 255, alpha),
                    width=4,
                )
            img.paste(vf, (pos_x, pos_y))
        except Exception:
            pass
        finally:
            if temp_frame.exists():
                temp_frame.unlink(missing_ok=True)

    # Aplica la tipografía nítida sobre la base 1080p
    composite_sharp_typography(
        img,
        output_image_path,
        headline,
        subtitle,
        width=width,
        height=height,
        clean_left_vignette=False,
    )
    return output_image_path


def upscale_and_clarify_thumbnail(
    src_image: Path,
    output_path: Path,
    target_w: int = 1920,
    target_h: int = 1080,
) -> Path:
    """
    Escala la miniatura de la IA a 1920x1080 Full HD con filtrado Lanczos y máscara de enfoque
    (UnsharpMask) para erradicar cualquier borrosidad o pixelado en YouTube, sin duplicar textos.
    """
    from PIL import ImageFilter, ImageEnhance

    im = Image.open(src_image).convert("RGB")
    im_1080 = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
    sharp = im_1080.filter(ImageFilter.UnsharpMask(radius=1.5, percent=125, threshold=2))
    enhancer = ImageEnhance.Sharpness(sharp)
    sharp = enhancer.enhance(1.1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".png":
        sharp.save(str(output_path), "PNG", optimize=True)
    else:
        sharp.save(str(output_path), "JPEG", quality=98, subsampling=0)
    return output_path


def create_thumbnails(
    video_path: Path,
    output_dir: Path,
    meta: dict,
    thumb_cfg: dict,
) -> dict:
    """
    Genera el set global de 3 variantes de miniaturas en calidad Full HD (1920x1080)
    con máxima nitidez y sin duplicar textos:
    1. miniatura_1_elementos.jpg: Widgets IA en 1920x1080 (Lanczos + UnsharpMask 4:4:4).
    2. miniatura_2_personaje.jpg: Desarrollador anime IA en 1920x1080 (Lanczos + UnsharpMask 4:4:4).
    3. miniatura_3_local.png: Fotograma real del video + tipografía nítida 1080p.
    """
    results = {}
    headline = meta.get("headline", "WINDOWS")
    subtitle = meta.get("subtitle", "3 APPS PRO")
    tech_info = meta.get("tech_info", {})
    tecnologia = tech_info.get("tech", "Software Tutorial")
    icon = tech_info.get("icon", "modern glowing tech emblem")
    model = thumb_cfg.get("gflow_model", "nano-pro")
    target_w = thumb_cfg.get("width", 1920)
    target_h = thumb_cfg.get("height", 1080)

    # 1. Prompts para IA
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

    (output_dir / "prompt_miniatura_v1_elementos.txt").write_text(prompt_tools, encoding="utf-8")
    (output_dir / "prompt_miniatura_v2_personaje.txt").write_text(prompt_character, encoding="utf-8")

    # Variante 1: Buscar archivo crudo generado por IA y procesar a 1080p
    raw_ai_1 = output_dir / "miniatura_1_elementos_raw.jpg"
    if not raw_ai_1.exists():
        raw_candidates = list(output_dir.glob("miniatura_1_elementos*.jpg")) + list(output_dir.glob("miniatura_1_elementos*.png"))
        raw_ai_1 = raw_candidates[0] if raw_candidates else None

    if not raw_ai_1 and thumb_cfg.get("provider", "gflow") == "gflow" and check_gflow_auth():
        p1 = output_dir / "miniatura_1_elementos_raw.jpg"
        if generate_flow_thumbnail(prompt_tools, p1, model=model):
            raw_ai_1 = p1

    if raw_ai_1 and raw_ai_1.exists():
        out_v1_jpg = output_dir / "miniatura_1_elementos.jpg"
        out_v1_png = output_dir / "miniatura_1_elementos.png"
        upscale_and_clarify_thumbnail(raw_ai_1, out_v1_jpg, target_w=target_w, target_h=target_h)
        upscale_and_clarify_thumbnail(raw_ai_1, out_v1_png, target_w=target_w, target_h=target_h)
        results["ia_elementos"] = out_v1_jpg

    # Variante 2: Buscar archivo crudo generado por IA y procesar a 1080p
    raw_ai_2 = output_dir / "miniatura_2_personaje_raw.jpg"
    if not raw_ai_2.exists():
        raw_candidates_2 = list(output_dir.glob("miniatura_2_personaje*.jpg")) + list(output_dir.glob("miniatura_2_personaje*.png"))
        raw_ai_2 = raw_candidates_2[0] if raw_candidates_2 else None

    if not raw_ai_2 and thumb_cfg.get("provider", "gflow") == "gflow" and check_gflow_auth():
        p2 = output_dir / "miniatura_2_personaje_raw.jpg"
        if generate_flow_thumbnail(prompt_character, p2, model=model):
            raw_ai_2 = p2

    if raw_ai_2 and raw_ai_2.exists():
        out_v2_jpg = output_dir / "miniatura_2_personaje.jpg"
        out_v2_png = output_dir / "miniatura_2_personaje.png"
        upscale_and_clarify_thumbnail(raw_ai_2, out_v2_jpg, target_w=target_w, target_h=target_h)
        upscale_and_clarify_thumbnail(raw_ai_2, out_v2_png, target_w=target_w, target_h=target_h)
        results["ia_personaje"] = out_v2_jpg

    # Variante 3 (Local con fotograma real en 1920x1080)
    local_path = output_dir / "miniatura_3_local.png"
    generate_local_thumbnail(video_path, local_path, headline, subtitle, width=target_w, height=target_h)
    results["local_fotograma"] = local_path

    return results
