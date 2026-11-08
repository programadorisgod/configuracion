# 🛠️ Configuraciones y Dotfiles

Repositorio centralizado de configuraciones de sistema, entornos gráficos, aceleración por hardware, automatización multimedia y herramientas de terminal para entornos **Windows** y **Linux**.

---

## 📂 Estructura del Repositorio

El repositorio se organiza de forma modular en tres pilares principales:

```text
configuracion/
├── windows/
│   ├── terminal/
│   │   ├── alacritty/              # Emulador de terminal acelerado por GPU (OpenGL)
│   │   └── zellij/                 # Multiplexor de terminal (pestañas y paneles divididos)
│   ├── setup.ps1                   # Script de despliegue automatizado e instalación winget
│   └── README.md                   # Documentación, atajos y configuración en Windows
│
├── obs-pipeline/                   # Pipeline automatizado de post-producción OBS Studio
│   ├── scripts/                    # Scripts de ejecución (setup y daemon watcher en PowerShell y Bash)
│   ├── src/obs_pipeline/           # Módulos Python (audio EBU R128, subtítulos Whisper, miniaturas, SEO)
│   └── README.md                   # Documentación de post-producción automatizada
│
└── linux/
    ├── haswell-optimization/       # Optimizaciones de video VA-API, Zen Browser y PipeWire
    ├── perf-kit/                   # Suite CLI para optimización de kernel, ZRAM y planificador BPF
    ├── omarchy-hyde-blue/          # Dotfiles de escritorio Wayland (Hyprland, Waybar, temas)
    └── README.md                   # Índice técnico de configuraciones para Linux
```

---

## ⚡ Navegación Rápida

### 🪟 [Windows (Terminal Alacritty & Zellij)](windows/README.md)
- **Terminal de Alto Rendimiento**: Alacritty v0.17+ con renderizado por hardware, paleta Catppuccin Mocha, transparencia acrílica y fuente Cascadia Code con ligaduras.
- **Multiplexor Integrado**: Zellij v0.45+ con gestión de pestañas superiores, divisiones de paneles (splits verticales y horizontales) y navegación por teclado y ratón.
- **Despliegue en 1 Clic**: Script PowerShell (`setup.ps1`) que aprovisiona las configuraciones automáticamente en `%APPDATA%` e instala los paquetes necesarios vía `winget`.

### 🎬 [OBS Post-Production Pipeline](obs-pipeline/README.md)
- **Audio Studio Master**: Corrección automática de canales, reducción de ruido (`afftdn`), de-clicker (`adeclick`) y normalización EBU R128 (`-16 LUFS`).
- **Video Smart-Trim**: Detección y recorte de silencios iniciales/finales por *Stream Copy* (sin pérdida de calidad y en segundos).
- **Subtítulos con IA**: Transcripción rápida local en CPU con `faster-whisper` (int8) exportando a `.srt`, `.vtt` y `.txt`.
- **Miniaturas & SEO**: Generación de miniaturas 16:9 con Google Flow y generación automática de metadatos (títulos, timestamps y descripción para YouTube).

### 🐧 [Linux (Haswell, Perf-Kit & Hyprland)](linux/README.md)
- **Optimizaciones Haswell**: Ajustes específicos para procesadores Intel de 4ta generación (Intel HD 4600) para decodificación VA-API por hardware en navegadores y PipeWire sin chasquidos.
- **Linux Performance Kit (`perf-kit`)**: Suite CLI modular para ZRAM (`zstd`), optimizaciones de I/O en Btrfs/SSD, TCP BBR y planificadores `sched_ext` (`scx_bpfland`).
- **Omarchy Hyde Blue**: Entorno de escritorio Wayland con paleta de color azul cian (`#28b6f6`), barra Waybar flotante con widgets interactivos y fondos de pantalla rotativos.

---

## 🚀 Despliegue Rápido

### En Windows
Clona el repositorio y ejecuta el script de aprovisionamiento:
```powershell
git clone https://github.com/programadorisgod/configuracion.git
cd configuracion\windows
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

*(Para instalar automáticamente Alacritty y Zellij si no los tienes: `.\setup.ps1 -InstallPackages`)*

### En Linux
```bash
git clone https://github.com/programadorisgod/configuracion.git
cd configuracion/linux
./perf-kit/bin/perf-kit help
```

---

## 📄 Licencia

Distribuido bajo licencia MIT. Consulta el archivo correspondiente a cada módulo para directivas de uso específicas.
