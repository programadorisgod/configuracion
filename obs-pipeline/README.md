# OBS Post-Production Pipeline (Windows & Linux)

Pipeline modular, de alto rendimiento y 100% automatizado para procesar grabaciones de **OBS Studio** en entornos **Windows** y **Linux (CachyOS / Hyprland)**.

Optimizado específicamente para procesadores Intel sin tarjeta gráfica dedicada (Haswell i5-4590S / HD 4600 y gráficos Intel UHD).

---

## ⚡ ¿Qué hace este Pipeline?

Al terminar de grabar en OBS, el pipeline toma el video crudo y entrega una carpeta completa lista para publicar en YouTube o redes:

1. **🔊 Audio Studio Master**:
   - Diagnóstico automático de canales mono/estéreo (`pan=stereo|c0=c0|c1=c0` si un canal quedó mudo en OBS).
   - Filtro de corte de paso alto (`highpass=f=80`) para eliminar retumbos y zumbido eléctrico.
   - Eliminación de chasquidos de boca/teclado (`adeclick`).
   - Reducción de ruido constante (`afftdn`).
   - Compresor de voz y normalización de volumen profesional EBU R128 (`-16 LUFS`).
2. **✂️ Video Smart-Trim & Incrustación**:
   - Detección y recorte de silencios iniciales y finales (`silencedetect`).
   - Ensamblado por *Stream Copy* (`-c:v copy`), **cero pérdida de calidad y renderizado en segundos**.
   - Incrustación de subtítulos suaves (*soft-subs* seleccionables en reproductores) dentro del contenedor MP4.
3. **📝 Subtítulos con IA en CPU (`faster-whisper` int8)**:
   - Transcripción rápida limitada a 3 hilos de CPU para no congelar el sistema ni la reproducción de audio.
   - Exporta archivos `.srt`, `.vtt` y `.txt` con marcas de tiempo legibles (`[00:15]`).
   - Libera la memoria RAM inmediatamente al terminar.
4. **🎨 Miniatura 16:9 con Google Flow (`gflow-cli`)**:
   - Generación de miniaturas de alta conversión usando **Google Flow (Nano Banana 2.1)** a través de `gflow-cli`.
   - Plantilla de estilo 2D Flat Vector / Cel-Shaded estilo anime con titular en degradado naranja-amarillo, pastilla azul eléctrico y sujeto dinámico adaptado al tema del video.
   - Generador local gráfico de respaldo para funcionamiento 100% offline.
5. **🚀 Paquete de Títulos y Metadatos SEO**:
   - 10 Propuestas de títulos categorizadas por enfoque (Tutorial, Solución de Problemas, Directo y Curiosidad).
   - Capítulos con timestamps para YouTube (`00:00 Introducción`, `01:45 ...`).
   - Descripción lista para pegar y etiquetas (tags).

---

## 🚀 Instalación Rápida

### En Windows
Abre una terminal de PowerShell en esta carpeta y ejecuta:
```powershell
.\scripts\setup.ps1
```

### En Linux (CachyOS / Arch)
Abre una terminal en esta carpeta y ejecuta:
```bash
chmod +x scripts/*.sh
./scripts/setup.sh
```

---

## 💻 Uso

### 1. Diagnóstico del sistema (`doctor`)
Verifica FFmpeg, encoders por hardware, hilos seguros de CPU y sesión de Google Flow:
```bash
uv run obs-pipe doctor
```

### 2. Procesar un video bajo demanda (`process`)
```bash
uv run obs-pipe process "C:\Ruta\A\Tu\Video.mp4"
```
O con el script de acceso directo:
```bash
# Windows
.\scripts\obs-pipe.ps1 process "C:\Ruta\A\Tu\Video.mp4"

# Linux
./scripts/obs-pipe.sh process "~/Descargas/Video.mp4"
```

### 3. Modo Vigilante de Carpeta (`watch`)
Monitorea la carpeta de grabaciones de OBS y procesa automáticamente cada vez que detienes una grabación:
```bash
uv run obs-pipe watch
```

---

## 🎨 Configuración de Google Flow (`gflow-cli`)

Para habilitar la generación de miniaturas con Google Flow sin gastar créditos:
1. Inicia sesión en Google Flow por única vez desde la terminal:
   ```bash
   gflow auth login --browser chrome
   ```
2. Comprueba el estado de la sesión:
   ```bash
   gflow auth status
   ```
3. Puedes personalizar la plantilla de prompt en `config.toml` bajo la sección `[thumbnail]`.
