# Omarchy Hyde Blue Dotfiles

Configuración personalizada para Omarchy / Hyprland inspirada en la línea estética **HyDE**, optimizada para máximo rendimiento gráfico (Intel Haswell i5-4590S / HD 4600 en configuración multimonitor) con cero pérdida de fluidez.

---

## Características Principales

1. **Estilo Visual HyDE**:
   - Color de acento principal: `#28b6f6` (azul celeste vibrante) y cian `#00e5ff`.
   - Fondo oscuro `#111622` para consistencia y descanso visual.
   - Esquinas redondeadas (`rounding = 10`, `border-radius: 14px`) en ventanas, barra superior, menú y notificaciones.
   - Bordes de ventana con gradiente dinámico a 45°.
   - Redimensionamiento de ventanas arrastrando con el ratón directamente desde cualquier borde.

2. **Header Bar (Waybar) en Píldoras Flotantes**:
   - Barra con módulos en islas flotantes translúcidas separadas del borde de la pantalla.
   - **Calendario interactivo al dar clic**: Widget en Wayland Layer Shell (`calendar-popup.py`) con canal alfa ARGB 32-bit (sin cuadros negros ni parpadeos). Se abre al dar clic al reloj y se cierra con otro clic, botón de cierre o tecla `Escape`.

3. **Ventanas Híbridas Inteligentes**:
   - Gestor de archivos (`Nautilus`), diálogos, visores de imágenes y controles del sistema abren automáticamente flotantes y centrados.
   - Atajo `SUPER + ALT + ENTER` para terminal rápida flotante.
   - Atajo `SUPER + T` para alternar cualquier ventana entre flotante y mosaico (tiling).

4. **Rotación Diaria Automática de Fondos de Pantalla**:
   - Servicio y temporizador de systemd (`daily-wallpaper.timer` + `daily-wallpaper.service`).
   - Rota automáticamente el fondo de pantalla cada día a medianoche (o al iniciar el equipo si estuvo apagado).
   - Incluye pack de fondos azules y el arte horizontal de Adventure Time (Finn & Jake's Treehouse).

5. **Optimización de Rendimiento Intel Haswell**:
   - `blur`, `shadow` y animaciones pesadas desactivadas para conservar 60 FPS estables en 2 pantallas.
   - Opacidad al 100% (sin mezclas alfa que sobrecarguen la GPU).
   - Direct scanout (`direct_scanout = 1`) y aceleración por hardware VA-API Intel `i965`.

---

## Atajos de Teclado Útiles

| Atajo | Acción |
| :--- | :--- |
| `SUPER + RETURN` | Terminal principal (mosaico) |
| `SUPER + ALT + RETURN` | Terminal flotante centrada |
| `SUPER + SHIFT + F` | Gestor de archivos Nautilus (flotante) |
| `SUPER + SHIFT + RETURN` | Navegador web (Zen / Browser) |
| `SUPER + T` | Alternar ventana actual entre flotante y mosaico |
| `SUPER + O` | Fijar ventana flotante (Modo PiP / Pop-out) |
| `SUPER + W` | Cerrar ventana activa |
| `Clic en reloj` | Abrir / Cerrar calendario emergente |
| `Escape` | Cerrar calendario emergente |

---

## Instalación

Dentro del directorio `linux/omarchy-hyde-blue`:

```bash
chmod +x install.sh
./install.sh
```
El instalador despliega automáticamente las configuraciones en `~/.config/` y activa el temporizador systemd de rotación de fondos de pantalla.
