# Configuraciones y Dotfiles

Repositorio centralizado de configuraciones de sistema, entornos gráficos, aceleración por hardware y herramientas de terminal para entornos **Windows** y **Linux**.

---

## Estructura del Repositorio

El repositorio se divide en dos áreas principales según la plataforma:

```text
configuracion/
├── windows/
│   ├── terminal/
│   │   ├── alacritty/              # Emulador de terminal acelerado por GPU (OpenGL)
│   │   └── zellij/                 # Multiplexor de terminal (pestañas y paneles divididos)
│   ├── setup.ps1                   # Script de aprovisionamiento automatizado
│   └── README.md                   # Documentación y atajos para Windows
│
└── linux/
    ├── haswell-optimization/       # Optimizaciones de video VA-API, Zen Browser y PipeWire
    ├── perf-kit/                   # Suite CLI para optimización de kernel, ZRAM y planificador BPF
    ├── omarchy-hyde-blue/          # Dotfiles de escritorio Wayland (Hyprland, Waybar, temas)
    └── README.md                   # Índice técnico de configuraciones para Linux
```

---

## Navegación Rápida

### [Windows](windows/README.md)
- **Terminal moderna**: Alacritty configurado con tema Catppuccin Mocha, transparencia acrílica y fuente Cascadia Code.
- **Pestañas y splits**: Zellij integrado para gestión de múltiples sesiones, división de pantalla y soporte de ratón.
- **Instalación**: Script PowerShell (`setup.ps1`) para enlazar las configuraciones automáticamente en `%APPDATA%`.

### [Linux](linux/README.md)
- **Optimizaciones Haswell**: Ajustes específicos para procesadores Intel de 4ta generación (Intel HD 4600) en Linux para decodificación por hardware H.264, eliminación de deadlocks en navegadores y configuración de audio sin cortes.
- **Linux Performance Kit (`perf-kit`)**: Herramienta de línea de comandos para aplicar y revertir ajustes de memoria (ZRAM `zstd`), I/O (Btrfs/SSD), algoritmos de red TCP BBR y planificadores `sched_ext` (`scx_bpfland`).
- **Omarchy Hyde Blue**: Entorno de escritorio Wayland con paleta de color azul cian (`#28b6f6`), barra Waybar en píldoras flotantes con widget de calendario interactivo y rotador diario de fondos de pantalla.

---

## Licencia

Distribuido bajo licencia MIT. Consulta el archivo correspondiente a cada módulo para directivas de uso específicas.
