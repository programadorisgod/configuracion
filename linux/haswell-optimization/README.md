# Guía de Optimización de Rendimiento de Software

### Para Intel Core i5-4590S (Haswell 4C/4T) + Intel HD Graphics 4600
**Sistema Operativo:** CachyOS Linux (Kernel 7.2.x) | **Entorno:** Hyprland / Omarchy (Wayland) | **Configuración:** Dual Monitor (1600x900 + 1280x1024)

---

## 1. Diagnóstico Inicial del Problema

A pesar de contar con 4 núcleos físicos y 8 GB de RAM, el equipo sufría saturación de **CPU al 100%**, congelamientos en Google Meet/Discord y lentitud extrema con 2 o 3 pestañas. Las causas identificadas fueron:

1. **Aceleración por Hardware Incompatible (VA-API):** El sistema intentaba cargar `intel-media-driver` (`iHD`), el cual no soporta Haswell (Gen 7.5). Además, faltaba `LIBVA_DRIVER_NAME=i965`.
2. **Video por Software en CPU:** Google Meet, Discord y YouTube negociaban por defecto códecs modernos (**VP9** y **AV1**). Dado que la GPU Intel HD 4600 solo soporta **H.264** en hardware, el procesamiento caía 100% en los 4 núcleos de la CPU.
3. **Sobrecarga de Hyprland en 2 Monitores:** La configuración de fábrica forzaba transparencia (`0.97 / 0.90`) en todas las ventanas, desenfoque *Kawase* de 2 pasadas, sombras y animaciones, consumiendo hasta un 10% de CPU continua y bloqueando el *Direct Scanout*.
4. **Cortes de Voz en Discord y Meet:** El buffer por defecto de PipeWire era demasiado bajo bajo carga de CPU, causando *underruns* (voz robotizada y microcortes).
5. **Servicios Innecesarios en Segundo Plano:** El indexador de archivos `localsearch-3` (Tracker) y el servicio de impresión `cups` consumían I/O y ciclos de CPU.

---

## 2. Optimizaciones Aplicadas

### A. Compositor Gráfico (Hyprland / Omarchy)
**Archivo:** `~/.config/hypr/looknfeel.lua` *(Respaldo en `looknfeel.lua.bak.*`)*
* **Variables de video:** Forzado de driver de video Haswell a nivel de Wayland (`LIBVA_DRIVER_NAME = "i965"`, `VDPAU_DRIVER = "va_gl"` y `MOZ_DRM_DEVICE = "/dev/dri/renderD128"`).
* **Efectos pesados:** Desactivados `blur`, `shadow` y `animations`.
* **Direct Scanout:** Activado `render.direct_scanout = 1` para aplicaciones a pantalla completa.
* **Transparencias eliminadas:** Se forzó `opacity = "1.0 1.0"` en ventanas, navegadores y terminales para eliminar la mezcla de canales alfa en ambos monitores.

**Archivo:** `~/.config/hypr/hyprlock.conf`
* `blur_passes = 0` para evitar picos de GPU al bloquear la pantalla.

---

### B. Variables Globales de Sesión
**Archivo:** `~/.config/environment.d/10-vaapi.conf`
Asegura que cualquier aplicación lanzada vía `systemd`, `uwsm` o atajos de teclado herede el driver correcto de video:
```ini
LIBVA_DRIVER_NAME=i965
VDPAU_DRIVER=va_gl
MOZ_DRM_DEVICE=/dev/dri/renderD128
```

---

### C. Zen Browser (Navegador Principal)
**Archivo:** `~/.config/zen/<perfil>.Default (release)/user.js` *(plantilla en `configs/zen/user.js`)*

1. **Aceleración VA-API de Video en GPU (Sin Forzado en DRM):**
   - `media.ffmpeg.vaapi.enabled = true` y `media.hardware-video-decoding.enabled = true`: Activa la decodificación por hardware de la GPU Intel HD 4600.
   - `media.hardware-video-decoding.force-enabled = false`: Crucial para DRM. En Linux, los drivers de VA-API no soportan descifrado de flujos protegidos. Dejarlo en `false` permite que YouTube/Meet usen VA-API en hardware, mientras que Prime Video y Netflix usan Widevine CDM sin congelarse en el botón Play.
   - `media.rdd-ffmpeg.enabled = false` y `media.rdd-process.enabled = false`: Crucial para estabilidad. El proceso sandbox RDD (Remote Data Decoder) sufre un *deadlock* documentado con el driver `i965` de Haswell que congelaba la interfaz tras unos momentos de reproducción. Desactivarlo decodifica directamente sin bloqueos de UI.
   - `gfx.webrender.all = true`
2. **Google Meet y Discord Fluidos (WebRTC por Hardware):**
   - `media.webrtc.hw.h264.enabled = true` y `media.navigator.mediadatadecoder_h264_enabled = true`: Delega la codificación y decodificación de llamadas al chip QuickSync H.264 de la GPU.
   - `media.peerconnection.video.vp9_enabled = false`: Impide que Meet o Discord fuercen VP9 por software en la CPU.
   - `media.mediasource.vp9.enabled = true`: Mantiene activa la compatibilidad MSE para evitar que las tarjetas y vistas previas de Prime Video rompan sus scripts.
3. **Soporte DRM Widevine (Prime Video, Netflix, Spotify Web):**
   - `media.eme.enabled = true`
   - `media.gmp-widevinecdm.enabled = true` y `visible = true`
4. **WebGPU y WebGL:**
   - `dom.webgpu.enabled = true` y `gfx.webgpu.ignore-blocklist = true`: Salta la lista de bloqueo de Mesa para Haswell Vulkan 1.2 y evita caer en SwiftShader por CPU.
   - `webgl.force-enabled = true`
5. **Gestión de Memoria y UI Accesible:**
   - `dom.ipc.processCount = 4` y `dom.ipc.processCount.webIsolated = 2`: Evita la proliferación de procesos pesados en 8 GB de RAM.
   - `browser.tabs.unloadOnLowMemory = false`: Evita que el navegador congele o suspenda la pestaña activa de streaming.
   - `accessibility.force_disabled = 0`: Garantiza el correcto funcionamiento de clics en popups de permisos.

---

### D. Google Chrome / Chromium / Electron
**Archivos:** `~/.config/chrome-flags.conf`, `chromium-flags.conf` y `electron-flags.conf`
```ini
--ozone-platform=wayland
--ozone-platform-hint=wayland
--ignore-gpu-blocklist
--enable-gpu-rasterization
--enable-zero-copy
--enable-unsafe-webgpu
--use-cmd-decoder=validating
--renderer-process-limit=4
--enable-features=VaapiVideoDecoder,VaapiVideoEncoder,VaapiIgnoreDriverChecks,AcceleratedVideoDecodeLinuxGL,AcceleratedVideoDecodeLinuxZeroCopyGL,AcceleratedVideoEncoder,WebRTCPipeWireCapturer,Vulkan,VulkanFromANGLE,DefaultANGLEVulkan,TouchpadOverscrollHistoryNavigation
--disable-features=UseChromeOSDirectVideoDecoder
```

---

### E. Audio sin Cortes en Discord y Meet (PipeWire)
**Archivo:** `~/.config/pipewire/pipewire.conf.d/99-low-cpu-audio.conf`
Aumenta el quantum mínimo a 512 (aprox. 10.6 ms a 48 kHz) para evitar interrupciones o voz robótica cuando la CPU tiene picos de trabajo:
```ini
context.properties = {
    default.clock.rate          = 48000
    default.clock.quantum       = 1024
    default.clock.min-quantum   = 512
    default.clock.max-quantum   = 2048
}
```

---

### F. Servicios en Segundo Plano Desactivados
1. **Indexador de archivos:**
   ```bash
   systemctl --user mask --now localsearch-3.service
   ```
2. **Servicio de impresoras:**
   ```bash
   sudo systemctl disable --now cups.service cups-browsed.service cups.socket cups.path
   ```

---

### G. Optimización de Grabación en OBS Studio (QuickSync VA-API)
**Archivo:** `~/.config/obs-studio/basic/profiles/<perfil>/basic.ini` *(plantilla en `configs/obs-studio/basic.ini`)*

Por defecto, OBS Studio graba por CPU (**x264**), lo que en un procesador de 4 hilos (i5-4590S) satura el uso de CPU al 100% y produce tirones o pérdida de fotogramas.

#### Configuración Aplicada:
1. **Modo de salida:** Cambiado de `Sencillo` a **`Avanzado`** en la pestaña **Grabación**.
2. **Codificador de video por Hardware:** Seleccionar **`FFmpeg VAAPI (H.264)`** (`ffmpeg_vaapi_tex`). Delega la compresión de video al chip de silicio dedicado Intel QuickSync de la gráfica integrada HD 4600.
3. **Control de la frecuencia (Calidad):**
   - Modo: **CQP** (Constant Quality Parameter) en lugar de CBR.
   - Nivel de CQP: **`20` - `22`** (calidad visual idéntica al original con bordes nítidos para código/texto y mínimo peso).
   - Intervalo de fotogramas clave: `2 s`.
4. **Resolución y Rendimiento:**
   - **Resolución base (lienzo):** `1600x900`
   - **Resolución de salida:** `1600x900` (sin escalar, evitando carga innecesaria de GPU).
   - **FPS Comunes:** `48` fps (o `30` fps para tutoriales/programación; `60` fps para juegos).
5. **Captura Wayland y optimización visual:**
   - Fuente de captura: **Captura de pantalla (PipeWire)** nativa de Wayland.
   - **Desactivar vista previa en vivo:** Clic derecho sobre el lienzo de OBS y desmarcar *Habilitar vista previa* durante grabaciones largas (ahorra ~10-15% de GPU).

#### Resultado:
* **Uso de CPU:** Reducido de **90-100%** a solo **5% - 15%** mientras graba pantalla a máxima calidad.

---

## 3. Comandos de Verificación y Diagnóstico

Para comprobar en cualquier momento que las optimizaciones siguen activas:

* **Verificar VA-API de la GPU:**
  ```bash
  LIBVA_DRIVER_NAME=i965 vainfo
  # Debe indicar: "Driver version: Intel i965 driver for Intel(R) Haswell Desktop"
  ```
* **Verificar opciones de Hyprland:**
  ```bash
  hyprctl getoption decoration:blur:enabled      # Debe ser: false
  hyprctl getoption decoration:shadow:enabled    # Debe ser: false
  hyprctl getoption animations:enabled           # Debe ser: false
  hyprctl getoption render:direct_scanout        # Debe ser: 1
  hyprctl configerrors                           # Debe estar vacío (0 errores)
  ```
* **Verificar latencia de PipeWire:**
  ```bash
  pw-metadata -n settings 0 clock.min-quantum    # Debe reportar: value: '512'
  ```

---

## 4. Reversión de Cambios

Todos los cambios fueron configurados de forma modular y no destructiva:
* **Hyprland:** Restaurar el archivo `~/.config/hypr/looknfeel.lua.bak.<timestamp>` sobre `looknfeel.lua` y ejecutar `hyprctl reload`.
* **Zen Browser:** Eliminar `~/.config/zen/<perfil>.Default (release)/user.js` y reiniciar el navegador.
* **Chrome / Electron:** Eliminar `~/.config/chrome-flags.conf` y `electron-flags.conf`.
* **PipeWire:** Eliminar `~/.config/pipewire/pipewire.conf.d/99-low-cpu-audio.conf` y ejecutar `systemctl --user restart pipewire pipewire-pulse`.
* **Servicios:** Reactivar con `systemctl --user unmask --now localsearch-3.service` y `sudo systemctl enable --now cups.service`.
