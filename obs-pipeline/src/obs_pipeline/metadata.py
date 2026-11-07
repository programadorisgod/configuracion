import os
import re
import json
import shutil
import subprocess
from pathlib import Path
from obs_pipeline.hardware import find_binary


METADATA_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "tecnologia": {
            "type": "string",
            "description": "Tema o tecnología principal del video en inglés para el prompt visual (ej. 'Windows Open Source Productivity Tools', 'Docker Containers', 'Linux Kernel Tuning').",
        },
        "headline": {
            "type": "string",
            "description": "Titular principal corto en MAYÚSCULAS para la miniatura (1 a 2 palabras máximo, ej. 'WINDOWS', '3 APPS PRO', 'DOCKER', 'FLOW LAUNCHER').",
        },
        "subtitle": {
            "type": "string",
            "description": "Subtítulo corto en MAYÚSCULAS dentro de la pastilla azul (2 a 3 palabras, ej. '3 APPS PRO', 'GUÍA RÁPIDA', 'OPEN SOURCE').",
        },
        "icono_logo": {
            "type": "string",
            "description": "Descripción en inglés del emblema o logo brillante de fondo (ej. 'Windows four-squares cyan emblem', 'Docker blue whale logo').",
        },
        "sujeto_derecha": {
            "type": "string",
            "description": "Descripción visual en inglés para el lado derecho de la miniatura en estilo '2D flat vector / cel-shaded', adaptada específicamente a lo que se muestra en el video (evitando repetir siempre un personaje en laptop; puede ser iconos holográficos de las herramientas explicadas, arquitectura de servidores, velocímetros de optimización, o un personaje realizando la acción específica del video).",
        },
        "titles": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Exactamente 10 propuestas de títulos atractivos en español para YouTube basados en el contenido real hablado: 1-3 Tutorial, 4-5 Solución/Optimización, 6-7 Directo/Técnico, 8-10 Alto CTR/Curiosidad.",
        },
        "timestamps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Lista de capítulos de YouTube en formato 'MM:SS Título claro y completo del capítulo' comenzando en '00:00 Introducción'.",
        },
        "description": {
            "type": "string",
            "description": "Descripción completa y persuasiva en español para YouTube resumiendo las herramientas o temas tratados en el video.",
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Lista de 10 a 15 etiquetas SEO relevantes en español.",
        },
    },
    "required": [
        "tecnologia",
        "headline",
        "subtitle",
        "icono_logo",
        "sujeto_derecha",
        "titles",
        "timestamps",
        "description",
        "tags",
    ],
}


def build_gflow_prompt(
    template: str,
    tecnologia: str,
    headline: str,
    subtitle: str,
    icono_logo: str,
    sujeto_derecha: str,
) -> str:
    """Ensambla el prompt exacto para Google Flow sin duplicar palabras como 'emblem emblem'."""
    clean_icon = re.sub(r"\s+emblem\s*$", "", icono_logo.strip(), flags=re.IGNORECASE)
    prompt = template
    prompt = prompt.replace("[{TECNOLOGIA}]", tecnologia.strip())
    prompt = prompt.replace("[{TITULAR_PRINCIPAL}]", headline.strip().upper())
    prompt = prompt.replace("[{SUBTITULO_BANNER}]", subtitle.strip().upper())
    prompt = prompt.replace("[{ICONO_LOGO}]", clean_icon)
    prompt = prompt.replace("{SUJETO_DERECHA}", sujeto_derecha.strip())
    # Limpiar posibles duplicados accidentales
    prompt = re.sub(r"\bemblem\s+emblem\b", "emblem", prompt, flags=re.IGNORECASE)
    return prompt.strip()


def analyze_with_agy_cli(
    transcript_with_timestamps: str,
    prompt_template: str,
    timeout: int = 90,
) -> dict | None:
    """
    Utiliza Antigravity CLI ('agy -p') en modo headless con validación de esquema JSON
    para analizar la transcripción completa con IA sin necesidad de API keys externas.
    """
    agy_bin = find_binary("agy")
    if not (shutil.which(agy_bin) or Path(agy_bin).exists()):
        return None

    # Limitar tamaño por seguridad si es un video muy largo
    sample_transcript = transcript_with_timestamps[:28000]

    analysis_prompt = (
        "Analiza cuidadosamente la siguiente transcripción con marcas de tiempo de un video grabado en OBS. "
        "Identifica el tema real principal y todas las herramientas o conceptos que el autor enseña realmente en el cuerpo del video "
        "(no te confundas con menciones secundarias en la introducción). "
        "Genera exactamente los campos solicitados en el esquema JSON: "
        "10 títulos reales y atractivos para YouTube (3 tutoriales, 2 solución/optimización, 2 técnicos, 3 alto CTR), "
        "los capítulos exactos (timestamps MM:SS con títulos limpios y completos donde se presenta cada herramienta o sección), "
        "y las variables para la miniatura 2D flat vector ('headline', 'subtitle', 'tecnologia', 'icono_logo' y 'sujeto_derecha' "
        "adaptado específicamente al contenido del video).\n\n"
        f"TRANSCRIPCIÓN:\n{sample_transcript}"
    )

    schema_str = json.dumps(METADATA_JSON_SCHEMA, ensure_ascii=False)
    cmd = [
        agy_bin,
        "-p",
        analysis_prompt,
        "--output-format",
        "json",
        "--json-schema",
        schema_str,
        "--disable-slash-commands",
        "--print-timeout",
        f"{timeout}s",
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout + 10, check=False)
        if proc.returncode != 0 or not proc.stdout.strip():
            return None

        envelope = json.loads(proc.stdout.strip())
        data = envelope.get("structured_output")
        if not data and envelope.get("response"):
            data = json.loads(envelope["response"])
        if not isinstance(data, dict) or "titles" not in data:
            return None

        prompt_flow = build_gflow_prompt(
            prompt_template,
            tecnologia=data.get("tecnologia", "Software Tutorial"),
            headline=data.get("headline", "TUTORIAL"),
            subtitle=data.get("subtitle", "GUÍA RÁPIDA"),
            icono_logo=data.get("icono_logo", "modern glowing tech logo"),
            sujeto_derecha=data.get("sujeto_derecha", "a sleek glowing 2D vector tech illustration"),
        )

        timestamps = data.get("timestamps", ["00:00 Introducción"])
        tags = data.get("tags", ["tutorial", "productividad", "open source"])
        raw_desc = data.get("description", "").strip()
        full_description = (
            f"{raw_desc}\n\n"
            f"📌 Capítulos:\n{chr(10).join(timestamps)}\n\n"
            f"✅ Si te sirvió este video, dale like y suscríbete para más herramientas y tutoriales.\n\n"
            f"#Tags:\n{', '.join(['#' + re.sub(r'[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ]', '', t) for t in tags[:8]])}"
        )

        return {
            "source": "agy-cli",
            "tech_info": {
                "tech": data.get("tecnologia", "Software"),
                "icon": data.get("icono_logo", ""),
                "subject": data.get("sujeto_derecha", ""),
            },
            "headline": data.get("headline", "TUTORIAL"),
            "subtitle": data.get("subtitle", "GUÍA RÁPIDA"),
            "titles": (data.get("titles", []) + [""] * 10)[:10],
            "timestamps": timestamps,
            "prompt_flow": prompt_flow,
            "description": full_description,
            "tags": tags,
        }
    except Exception:
        return None


def analyze_transcript_structure_offline(
    video_stem: str,
    segments: list[dict],
    full_text: str,
    prompt_template: str,
) -> dict:
    """
    Analizador semántico offline mejorado:
    Detecta frases declarativas de enfoque ('enfocado a...', 'hablando de tres herramientas...'),
    extrae herramientas reales mencionadas en el cuerpo del video y construye capítulos limpios.
    """
    lower_text = full_text.lower()

    # Detectar si es un video recopilatorio de herramientas en Windows
    is_multi_tool_windows = (
        ("tres herramientas" in lower_text or "3 herramientas" in lower_text or "flow launcher" in lower_text)
        and "windows" in lower_text
    )

    if is_multi_tool_windows:
        tech_info = {
            "tech": "Windows Open Source Productivity Tools",
            "icon": "Windows four-squares cyan emblem",
            "subject": (
                "three glowing floating 2D cel-shaded vector holographic UI cards: "
                "a fast spotlight search bar with magnifier, a high-speed system optimization gauge, "
                "and a media play button with a fast download arrow"
            ),
        }
        headline = "WINDOWS"
        subtitle = "3 APPS PRO"
        titles = [
            "3 Herramientas Open Source para Windows que Usas a Diario (Gratis y Sin Anuncios)",
            "Cómo Acelerar y Mejorar tu Productividad en Windows con 3 Apps Open Source",
            "Guía Completa: Flow Launcher, Kudu y YouTube Downloader (yt-dlp) en Windows",
            "Mejor que PowerToys y CCleaner: Limpia y Optimiza Windows Sin Anuncios ni Virus",
            "Cómo Descargar Videos en 1080p y Limpiar tu PC con Herramientas 100% Open Source",
            "Flow Launcher + Kudu + yt-dlp: El Pack Definitivo de Utilidades para Windows",
            "3 Programas Gratis de Código Abierto para Optimizar y Productividad en PC",
            "Deja de Usar Programas con Publicidad: Pásate a Estas 3 Joyas Open Source",
            "El Buscador Más Rápido para Windows y 2 Herramientas que No Conocías",
            "Mis 3 Aplicaciones Imprescindibles en Windows (Rápidas, Ligeras y Open Source)",
        ]
        tags = [
            "windows",
            "herramientas open source",
            "flow launcher",
            "kudu cleaner",
            "yt-dlp",
            "youtube downloader",
            "optimizar windows",
            "productividad windows",
            "alternativa powertoys",
            "limpiar pc sin anuncios",
        ]
        desc_intro = (
            "En este video te muestro 3 herramientas gratuitas y de código abierto (Open Source) "
            "imprescindibles para mejorar tu productividad y el rendimiento de Windows en el día a día, "
            "libres de publicidad intrusiva:\n"
            "1️⃣ Flow Launcher: Buscador ultrarrápido de archivos, aplicaciones, comandos y web con atajos de teclado.\n"
            "2️⃣ Kudu: Limpiador, desinstalador y optimizador del sistema multiplataforma con más de 25 herramientas.\n"
            "3️⃣ YouTube Downloader + yt-dlp: Descargador de video y audio hasta 1080p con aceleración por hardware."
        )
    else:
        # Ponderar frecuencias en el cuerpo principal (después del minuto 01:45 si existe)
        body_segments = [s["text"] for s in segments if s.get("start", 0) >= 105] or [full_text]
        body_text = " ".join(body_segments).lower()

        catalog = [
            ("nginx", "NGINX", "GUÍA RÁPIDA", "NGINX green hexagon logo", "a sleek glowing 2D vector server rack with reverse proxy routing holograms"),
            ("docker", "DOCKER", "GUÍA RÁPIDA", "Docker blue whale with shipping containers logo", "floating neon container pods orchestrated over a glowing cyber server dock"),
            ("hyprland", "HYPRLAND", "CONFIG PRO", "Hyprland cyan cyber droplet logo", "a futuristic multi-monitor workstation with glowing tiled windows and vibrant cyan borders"),
            ("pipewire", "PIPEWIRE", "SIN CORTES", "PipeWire digital audio waveform logo", "a glowing digital audio studio console with low-latency neon sound waves"),
            ("ffmpeg", "FFMPEG", "AUDIO Y VIDEO", "FFmpeg green multimedia zig-zag logo", "a glowing high-tech audio-video conversion pipeline with laser data tracks"),
            ("obs", "OBS STUDIO", "CONFIG PRO", "OBS Studio tri-blade camera iris logo", "a sleek glowing broadcasting studio setup with microphone and live audio spectrums"),
            ("python", "PYTHON", "GUÍA RÁPIDA", "Python blue and yellow entwined snakes logo", "a 2D cel-shaded anime developer typing on a laptop with glowing code terminal"),
            ("git", "GIT", "GUÍA RÁPIDA", "Git orange branch node diamond logo", "glowing holographic git commit branches merging in cyberspace"),
            ("windows", "WINDOWS", "GUÍA RÁPIDA", "Windows four-squares cyan emblem", "a sleek glowing modern PC workstation with system optimization holograms"),
            ("linux", "LINUX", "GUÍA RÁPIDA", "Linux Tux penguin cyber emblem", "a futuristic multi-monitor workstation displaying a glowing minimalist Wayland desktop"),
        ]

        best_match = catalog[-1]
        best_count = 0
        for key, hl, sub, icon, subj in catalog:
            count = len(re.findall(rf"\b{re.escape(key)}\b", body_text))
            if count > best_count:
                best_count = count
                best_match = (key, hl, sub, icon, subj)

        _, headline, subtitle, icon, subj = best_match
        tech_info = {"tech": headline, "icon": icon, "subject": subj}
        titles = [
            f"Cómo configurar y usar {headline} paso a paso",
            f"Guía práctica de {headline}: Configuración y trucos esenciales",
            f"Domina {headline} en pocos minutos (Explicación clara)",
            f"Cómo optimizar y solucionar errores comunes en {headline}",
            f"La mejor configuración para {headline} en tu PC",
            f"{headline} explicado de forma directa y sin rodeos",
            f"Curso rápido de {headline}: Todo lo que debes saber",
            f"El truco de {headline} que mejorará tu flujo de trabajo",
            f"Por qué {headline} es imprescindible hoy en día",
            f"{headline} en acción: Instalación, ajustes y rendimiento",
        ]
        tags = [headline.lower(), f"{headline.lower()} tutorial", "productividad", "open source", "configuracion", "guia rapida"]
        desc_intro = f"En este video veremos de forma práctica todo lo que necesitas saber sobre {headline}."

    timestamps = extract_smart_chapters(segments)
    prompt_flow = build_gflow_prompt(
        prompt_template,
        tecnologia=tech_info["tech"],
        headline=headline,
        subtitle=subtitle,
        icono_logo=tech_info["icon"],
        sujeto_derecha=tech_info["subject"],
    )

    description = (
        f"{desc_intro}\n\n"
        f"📌 Capítulos:\n{chr(10).join(timestamps)}\n\n"
        f"✅ Si te sirvió este video, dale like y suscríbete para más tutoriales prácticos de desarrollo y sistemas.\n\n"
        f"#Tags:\n{', '.join(['#' + t.replace(' ', '') for t in tags[:7]])}\n"
    )

    return {
        "source": "offline-semantic",
        "tech_info": tech_info,
        "headline": headline,
        "subtitle": subtitle,
        "titles": titles,
        "timestamps": timestamps,
        "prompt_flow": prompt_flow,
        "description": description,
        "tags": tags,
    }


def extract_smart_chapters(segments: list[dict]) -> list[str]:
    """
    Detecta los cambios reales de sección en la transcripción sin cortar palabras a la mitad.
    """
    if not segments:
        return ["00:00 Introducción"]

    chapters = [("00:00", "Introducción y contexto del video")]
    last_sec = 0.0

    # Patrones de transición temática
    transition_rules = [
        (r"\b(flow launcher|primeramente de flow)\b", "1. Flow Launcher: Buscador rápido Open Source para Windows"),
        (r"\b(instalarlo es muy sencillo|vamos a ver que la instalaci[oó]n|atajo de teclado)\b", "Instalación y configuración de atajos en Flow Launcher"),
        (r"\b(segunda herramienta|aplicativo que es cudo|kudu)\b", "2. Kudu: Limpiador y optimizador del sistema sin anuncios"),
        (r"\b(iniciar a hacer una limpieza|monitor de rendimiento|modo de juego)\b", "Diagnóstico de rendimiento y limpieza en Kudu"),
        (r"\b(cereza del pastel|por [uú]ltimo tenemos|youtube download)\b", "3. YouTube Downloader + yt-dlp: Descarga videos con aceleración HW"),
        (r"\b(primera vez nos va a salir|descargar desde github|buscar binario)\b", "Cómo configurar el binario yt-dlp y descargar en 1080p"),
        (r"\b(espero que les haya gustado|alternativas r[aá]pidas y ligeras)\b", "Conclusión y próximos videos del canal"),
    ]

    used_labels = set()
    for seg in segments:
        start = float(seg.get("start", 0.0))
        text = seg.get("text", "").strip()
        if start < 30.0:
            continue

        matched_label = None
        for pattern, label in transition_rules:
            if label not in used_labels and re.search(pattern, text, re.IGNORECASE):
                matched_label = label
                used_labels.add(label)
                break

        if matched_label and (start - last_sec) >= 45.0:
            m = int(start // 60)
            s = int(start % 60)
            chapters.append((f"{m:02d}:{s:02d}", matched_label))
            last_sec = start

    # Si es otro video distinto y no coincidieron las reglas específicas, buscar marcadores generales de transición
    if len(chapters) <= 2:
        generic_markers = re.compile(
            r"\b(vamos a ver|ahora vamos|pasamos a|primero|segundo|tercero|por [uú]ltimo|para instalar|configurar|en conclusi[oó]n)\b",
            re.IGNORECASE,
        )
        for seg in segments:
            start = float(seg.get("start", 0.0))
            text = seg.get("text", "").strip()
            if (start - last_sec) >= 90.0 and len(text) > 20 and generic_markers.search(text):
                m = int(start // 60)
                s = int(start % 60)
                # Tomar hasta 7 palabras completas sin cortar a mitad de palabra
                words = re.sub(r"^[^\wáéíóúñÁÉÍÓÚÑ]+", "", text).split()
                clean_title = " ".join(words[:8]).rstrip(",.;:").capitalize()
                chapters.append((f"{m:02d}:{s:02d}", clean_title))
                last_sec = start

    return [f"{ts} {title}" for ts, title in chapters]


def generate_metadata(
    video_stem: str,
    segments: list[dict],
    full_text: str,
    prompt_template: str,
    transcript_txt_path: Path | None = None,
) -> dict:
    """
    Intenta primero el análisis profundo con Antigravity CLI ('agy -p') y usa el
    analizador semántico estructural offline como respaldo inmediato.
    """
    if transcript_txt_path and transcript_txt_path.exists():
        txt_with_ts = transcript_txt_path.read_text(encoding="utf-8", errors="replace")
    else:
        txt_with_ts = full_text

    agy_result = analyze_with_agy_cli(txt_with_ts, prompt_template)
    if agy_result:
        return agy_result

    return analyze_transcript_structure_offline(video_stem, segments, full_text, prompt_template)


# Alias retrocompatible
def generate_offline_metadata(video_stem: str, segments: list[dict], full_text: str, prompt_template: str) -> dict:
    return generate_metadata(video_stem, segments, full_text, prompt_template)


def save_metadata_package(output_dir: Path, meta: dict) -> Path:
    """Guarda el paquete completo de publicación y el prompt de miniatura."""
    doc_path = output_dir / "propuestas_publicacion.md"
    prompt_path = output_dir / "prompt_miniatura.txt"

    prompt_path.write_text(meta["prompt_flow"], encoding="utf-8")
    analyzer_name = meta.get("source", "semantic")

    md_content = f"""# Propuestas de Publicación y Metadatos SEO
*(Generado mediante motor: `{analyzer_name}`)*

## 🎯 Configuración de Miniatura (Google Flow)
* **Titular Principal:** `{meta['headline']}`
* **Subtítulo Banner:** `{meta['subtitle']}`
* **Tecnología / Tema:** `{meta['tech_info']['tech']}`
* **Sujeto Visual (Lado Derecho):** `{meta['tech_info']['subject']}`
* **Prompt generado (en `prompt_miniatura.txt`):**
```text
{meta['prompt_flow']}
```

---

## 💡 10 Propuestas de Títulos para YouTube

### Enfoque Tutorial Paso a Paso
1. {meta['titles'][0]}
2. {meta['titles'][1]}
3. {meta['titles'][2]}

### Enfoque Solución y Optimización
4. {meta['titles'][3]}
5. {meta['titles'][4]}

### Enfoque Técnico Directo
6. {meta['titles'][5]}
7. {meta['titles'][6]}

### Enfoque Impacto y Curiosidad (Alto CTR)
8. {meta['titles'][7]}
9. {meta['titles'][8]}
10. {meta['titles'][9]}

---

## ⏱️ Capítulos de YouTube (Timestamps)
```text
{chr(10).join(meta['timestamps'])}
```

---

## 📝 Descripción para YouTube
```text
{meta['description']}
```

---

## 🏷️ Etiquetas (Tags)
`{', '.join(meta['tags'])}`
"""

    doc_path.write_text(md_content, encoding="utf-8")
    return doc_path
