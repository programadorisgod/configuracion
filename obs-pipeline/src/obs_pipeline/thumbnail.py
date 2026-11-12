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


def _find_best_font(size: int, prefer_impact: bool = True) -> ImageFont.FreeTypeFont:
    """Busca la tipografía más nítida disponible en el sistema (Windows/Linux)."""
    candidates = []
    if prefer_impact:
        candidates.extend([
            r"C:\Windows\Fonts\impact.ttf",
            "impact.ttf",
            "Impact.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            "arialbd.ttf",
            r"C:\Windows\Fonts\CascadiaCode.ttf",
            "DejaVuSans-Bold.ttf",
        ])
    else:
        candidates.extend([
            r"C:\Windows\Fonts\arialbd.ttf",
            "arialbd.ttf",
            r"C:\Windows\Fonts\CascadiaCode.ttf",
            "DejaVuSans-Bold.ttf",
            "impact.ttf",
        ])

    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_crisp_typography_overlay(
    target_w: int,
    target_h: int,
    headline: str,
    subtitle: str,
    scale: float = 2.0,
) -> Image.Image:
    """
    Renderiza la tipografía en un lienzo transparente a escala 2x (supersampling)
    y luego la reduce con filtro Lanczos para lograr bordes 100% vectoriales,
    degradados puros (#FFE600 -> #FF5000) y cero artefactos de pixelado.
    """
    sw = int(target_w * scale)
    sh = int(target_h * scale)
    canvas = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    headline_clean = headline.strip().upper()[:12]
    headline_pt = int(172 * scale) if len(headline_clean) <= 7 else int(136 * scale)
    font_headline = _find_best_font(headline_pt, prefer_impact=True)

    banner_clean = subtitle.strip().upper()[:20]
    banner_pt = int(64 * scale)
    font_banner = _find_best_font(banner_pt, prefer_impact=True)

    # Coordenadas maestras en escala 2x
    text_x = int(88 * scale)
    text_y = int(target_h * 0.28 * scale)

    # 1. Bounding box del titular
    bbox = draw.textbbox((0, 0), headline_clean, font=font_headline)
    tw = max(1, bbox[2] - bbox[0])
    th = max(1, bbox[3] - bbox[1] + int(30 * scale))

    # Sombra de profundidad 3D
    shadow_ox = int(10 * scale)
    shadow_oy = int(14 * scale)
    shadow_rad = int(12 * scale)
    for ox in range(-shadow_rad, shadow_rad + 1, int(3 * scale)):
        for oy in range(-shadow_rad, shadow_rad + 1, int(3 * scale)):
            draw.text(
                (text_x + shadow_ox + ox, text_y + shadow_oy + oy),
                headline_clean,
                font=font_headline,
                fill=(4, 8, 16, 120),
            )

    # Contorno exterior grueso afilado
    stroke_radius = int(11 * scale)
    for ox in range(-stroke_radius, stroke_radius + 1, int(2 * scale)):
        for oy in range(-stroke_radius, stroke_radius + 1, int(2 * scale)):
            if ox * ox + oy * oy <= stroke_radius * stroke_radius:
                draw.text(
                    (text_x + ox, text_y + oy),
                    headline_clean,
                    font=font_headline,
                    fill=(16, 8, 4, 255),
                )

    # Degradado vertical puro Amarillo Solar (#FFE600) -> Naranja Intenso (#FF4800)
    pad = int(16 * scale)
    mask = Image.new("L", (tw + pad * 2, th + pad * 2), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((pad - bbox[0], pad - bbox[1]), headline_clean, font=font_headline, fill=255)

    grad = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad)
    total_h = th + pad * 2
    for row in range(total_h):
        t = row / max(1, total_h - 1)
        r = 255
        g = int(230 * (1 - t) + 72 * t)
        b = int(10 * (1 - t))
        grad_draw.line([(0, row), (tw + pad * 2, row)], fill=(r, g, b, 255))

    canvas.paste(grad, (text_x - pad + bbox[0], text_y - pad + bbox[1]), mask)

    # 2. Pastilla de subtítulo Azul Eléctrico (#0072E8)
    banner_bbox = draw.textbbox((0, 0), banner_clean, font=font_banner)
    bw_text = banner_bbox[2] - banner_bbox[0]
    bh_text = banner_bbox[3] - banner_bbox[1]
    banner_w = max(int(460 * scale), bw_text + int(96 * scale))
    banner_h = int(108 * scale)
    banner_y = text_y + th + int(24 * scale)
    banner_radius = int(44 * scale)

    # Sombra sutil de la pastilla
    draw.rounded_rectangle(
        [
            text_x + int(4 * scale),
            banner_y + int(8 * scale),
            text_x + banner_w + int(4 * scale),
            banner_y + banner_h + int(8 * scale),
        ],
        radius=banner_radius,
        fill=(5, 10, 20, 150),
    )

    # Fondo azul eléctrico con borde cian brillante
    draw.rounded_rectangle(
        [text_x, banner_y, text_x + banner_w, banner_y + banner_h],
        radius=banner_radius,
        fill=(0, 114, 232, 255),
        outline=(56, 196, 255, 255),
        width=int(4 * scale),
    )

    # Texto blanco centrado nítido
    bx = text_x + (banner_w - bw_text) // 2 - banner_bbox[0]
    by = banner_y + (banner_h - bh_text) // 2 - banner_bbox[1]
    draw.text((bx, by), banner_clean, font=font_banner, fill=(255, 255, 255, 255))

    # Reducción con filtro Lanczos para anti-aliasing quirúrgico
    return canvas.resize((target_w, target_h), Image.Resampling.LANCZOS)


def compose_hybrid_thumbnail(
    background_source: Image.Image | Path,
    output_image_path: Path,
    headline: str,
    subtitle: str,
    target_res: tuple[int, int] = (1920, 1080),
) -> Path:
    """
    Compone una miniatura Ultra-HD combinando la ilustración/fondo (IA o fotograma)
    con el overlay tipográfico vectorial supersampleado (2x Lanczos).
    Aplica una sutil viñeta oscura en el tercio izquierdo para garantizar legibilidad 10/10.
    """
    target_w, target_h = target_res
    if isinstance(background_source, Path):
        base_img = Image.open(background_source).convert("RGBA")
    else:
        base_img = background_source.convert("RGBA")

    if base_img.size != (target_w, target_h):
        base_img = base_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Máscara de oscurecimiento suave en el tercio izquierdo (#091020 con degradado de alpha)
    dark_mask = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    d_draw = ImageDraw.Draw(dark_mask)
    fade_width = int(target_w * 0.48)
    for x in range(fade_width):
        t = x / max(1, fade_width - 1)
        # Transición suave polinómica: 220 a la izquierda -> 0 a la derecha
        alpha = int(225 * ((1.0 - t) ** 1.6))
        d_draw.line([(x, 0), (x, target_h)], fill=(9, 16, 32, alpha))

    base_img = Image.alpha_composite(base_img, dark_mask)

    # Superponer tipografía vectorial afilada
    overlay = render_crisp_typography_overlay(target_w, target_h, headline, subtitle, scale=2.0)
    final_img = Image.alpha_composite(base_img, overlay).convert("RGB")

    # Guardar en calidad máxima (PNG sin pérdida o JPEG 98 4:4:4)
    if output_image_path.suffix.lower() == ".png":
        final_img.save(str(output_image_path), "PNG", optimize=True)
    else:
        final_img.save(str(output_image_path), "JPEG", quality=98, subsampling=0)

    return output_image_path


def generate_local_thumbnail(
    video_path: Path,
    output_image_path: Path,
    headline: str,
    subtitle: str,
    target_res: tuple[int, int] = (1920, 1080),
) -> Path:
    """
    Genera localmente una miniatura Ultra-HD de respaldo con fondo azul medianoche (#091020),
    trazos neón, captura representativa del video y tipografía vectorial supersampleada.
    """
    width, height = target_res
    img = Image.new("RGBA", (width, height), (9, 16, 32, 255))
    draw = ImageDraw.Draw(img)

    neon_lines = [
        ([(0, int(height * 0.12)), (int(width * 0.18), 0)], (0, 150, 255, 210), int(10 * width / 1920)),
        ([(int(width * 0.12), int(height * 0.10)), (int(width * 0.22), 0)], (255, 130, 0, 190), int(6 * width / 1920)),
        ([(int(width * 0.52), int(height * 0.16)), (int(width * 0.65), 0)], (0, 210, 255, 180), int(7 * width / 1920)),
        ([(int(width * 0.82), int(height * 0.18)), (int(width * 0.98), 0)], (255, 140, 0, 200), int(8 * width / 1920)),
        ([(int(width * 0.28), height), (int(width * 0.40), height - int(height * 0.18))], (0, 160, 255, 190), int(7 * width / 1920)),
        ([(int(width * 0.42), height), (int(width * 0.54), height - int(height * 0.18))], (255, 130, 0, 210), int(8 * width / 1920)),
        ([(int(width * 0.84), height), (width, height - int(height * 0.24))], (0, 210, 255, 210), int(10 * width / 1920)),
    ]
    for coords, color, w in neon_lines:
        draw.line(coords, fill=color, width=max(2, w))

    temp_frame = output_image_path.parent / "temp_frame.png"
    if extract_video_frame(video_path, temp_frame):
        try:
            vf = Image.open(temp_frame).convert("RGBA")
            vf_w = int(width * 0.46)
            vf_h = int(vf_w * 9 / 16)
            vf = vf.resize((vf_w, vf_h), Image.Resampling.LANCZOS)

            pos_x = width - vf_w - int(width * 0.04)
            pos_y = (height - vf_h) // 2
            for pad, alpha in [(12, 50), (7, 110), (3, 240)]:
                draw.rounded_rectangle(
                    [pos_x - pad, pos_y - pad, pos_x + vf_w + pad, pos_y + vf_h + pad],
                    radius=16,
                    outline=(0, 210, 255, alpha),
                    width=4,
                )
            img.paste(vf, (pos_x, pos_y))
        except Exception:
            pass
        finally:
            if temp_frame.exists():
                temp_frame.unlink(missing_ok=True)

    # Componer tipografía con el motor vectorial
    return compose_hybrid_thumbnail(img, output_image_path, headline, subtitle, target_res=target_res)


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

    res_str = thumb_cfg.get("resolution", "1920x1080").lower()
    target_res = (1920, 1080) if "1080" in res_str else (1280, 720)

    # 1. Prompt Variante 1 (Elementos temáticos / herramientas - Fondo e ilustración LIMPIOS sin texto)
    subject_tools = tech_info.get("subject", "three floating glowing holographic tech icons")
    prompt_tools_clean = (
        f"2D flat vector YouTube thumbnail background and illustration, 16:9 aspect ratio. {tecnologia} tutorial theme. "
        f"On the right side, {subject_tools}. "
        f"Behind it, a single clean glowing {icon}. "
        f"Deep midnight blue background, clean composition, high contrast, vibrant electric blue and bright orange neon accents, "
        f"bold outlines, minimal visual clutter, sharp graphic design. "
        f"The left 45% of the image is completely empty dark midnight blue copy space with subtle neon lines. "
        f"ABSOLUTELY NO TEXT, NO WORDS, NO LETTERS, completely text-free background."
    )

    # 2. Prompt Variante 2 (Desarrollador anime cel-shaded - Fondo e ilustración LIMPIOS sin texto)
    prompt_character_clean = (
        f"2D flat vector YouTube thumbnail background and illustration, 16:9 aspect ratio. {tecnologia} tutorial theme. "
        f"On the right side, a 2D cel-shaded anime developer typing on a laptop with glowing code terminal and floating neon tool widgets. "
        f"Behind him, a single clean glowing {icon}. "
        f"Deep midnight blue background, clean composition, high contrast, vibrant electric blue and bright orange neon accents, "
        f"bold outlines, minimal visual clutter, sharp graphic design. "
        f"The left 45% of the image is completely empty dark midnight blue copy space with subtle neon lines. "
        f"ABSOLUTELY NO TEXT, NO WORDS, NO LETTERS, completely text-free background."
    )

    # Guardar ambos prompts limpios para inspección
    (output_dir / "prompt_miniatura_v1_elementos.txt").write_text(prompt_tools_clean, encoding="utf-8")
    (output_dir / "prompt_miniatura_v2_personaje.txt").write_text(prompt_character_clean, encoding="utf-8")

    # Intentar generar variantes IA si hay sesión activa en gflow
    use_hybrid = thumb_cfg.get("use_hybrid_overlay", True)
    if thumb_cfg.get("provider", "gflow") == "gflow" and check_gflow_auth():
        p1_raw = output_dir / "temp_ia_v1.png"
        p1_final = output_dir / "miniatura_1_elementos.png"
        if generate_flow_thumbnail(prompt_tools_clean, p1_raw, model=model):
            if use_hybrid:
                compose_hybrid_thumbnail(p1_raw, p1_final, headline, subtitle, target_res=target_res)
                p1_raw.unlink(missing_ok=True)
            else:
                p1_raw.replace(p1_final)
            results["ia_elementos"] = p1_final

        p2_raw = output_dir / "temp_ia_v2.png"
        p2_final = output_dir / "miniatura_2_personaje.png"
        if generate_flow_thumbnail(prompt_character_clean, p2_raw, model=model):
            if use_hybrid:
                compose_hybrid_thumbnail(p2_raw, p2_final, headline, subtitle, target_res=target_res)
                p2_raw.unlink(missing_ok=True)
            else:
                p2_raw.replace(p2_final)
            results["ia_personaje"] = p2_final

    # Variante 3 (Siempre garantizada): Miniatura local con fotograma real y composición vectorial Ultra-HD
    local_path = output_dir / "miniatura_3_local.png"
    generate_local_thumbnail(video_path, local_path, headline, subtitle, target_res=target_res)
    results["local_fotograma"] = local_path

    return results
