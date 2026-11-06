# Configuraciones para Linux

Este directorio agrupa dotfiles, paquetes de optimización a nivel de kernel y configuraciones de entorno de escritorio orientadas a máxima fluidez y rendimiento.

---

## Módulos Disponibles

### 1. [haswell-optimization](haswell-optimization/README.md)
Guía y configuraciones específicas para procesadores Intel Core de 4ta generación (Haswell) con gráficos integrados Intel HD Graphics 4600:
- Forzado del driver VA-API correcto (`i965`) y deshabilitación de `intel-media-driver` incompatible.
- Configuración de Zen Browser (`user.js`) para aceleración por hardware en llamadas (WebRTC H.264), prevención de cuelgues del proceso RDD y compatibilidad con DRM Widevine (Netflix, Prime Video).
- Ajustes de PipeWire para evitar chasquidos y voz robotizada en Discord y Google Meet bajo carga del sistema.
- Perfil de OBS Studio para grabación en hardware sin sobrecargar la CPU.

### 2. [perf-kit](perf-kit/README.md)
Herramienta CLI modular y portable para ajuste del sistema operativo:
- **CPU**: Alternador de mitigaciones de hardware (`mitigations=off`) y carga del planificador BPF `scx_bpfland`.
- **Memoria**: Configuración agresiva de ZRAM con compresión `zstd` y afinamiento de MGLRU / THP en `madvise`.
- **Almacenamiento**: Optimización de límites de escritura sucia para SSDs SATA sin DRAM con Btrfs y scheduler `adios` / `mq-deadline`.
- **Red**: Algoritmo de congestión TCP BBR y `fq` para reducir bufferbloat.
- **Herramientas**: Comandos `apply`, `revert`, `benchmark` y `status`.

### 3. [omarchy-hyde-blue](omarchy-hyde-blue/README.md)
Entorno de escritorio Wayland basado en Hyprland con estética inspirada en HyDE:
- **Paleta visual**: Acento `#28b6f6` (azul cian) sobre fondo oscuro `#111622`.
- **Waybar**: Barra modular en islas flotantes con widget de calendario interactivo Layer Shell en Python (`calendar-popup.py`).
- **Rotación de fondos**: Servicio y timer de systemd para rotar diariamente entre la colección de wallpapers azules incluidos.
- **Ventanas inteligentes**: Reglas de ventana flotante automática para diálogos, visores y explorador de archivos.
- **Instalación**: Script ejecutable `install.sh`.
