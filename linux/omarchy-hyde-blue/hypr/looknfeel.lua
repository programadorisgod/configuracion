-- Modo Máximo Rendimiento + Estilo HyDE para Intel Haswell (i5-4590S / HD 4600)
-- Aceleración por hardware para video y cero sobrecarga gráfica

-- Forzar el driver VA-API correcto para Intel Gen 7.5 (Haswell)
hl.env("LIBVA_DRIVER_NAME", "i965")
hl.env("VDPAU_DRIVER", "va_gl")
hl.env("MOZ_DRM_DEVICE", "/dev/dri/renderD128")

hl.config({
  general = {
    gaps_in = 5,
    gaps_out = 10,
    border_size = 2,
    resize_on_border = true,
    hover_icon_on_border = true,
    layout = "dwindle",
  },

  decoration = {
    rounding = 10,
    rounding_power = 2.0,
    dim_inactive = false,
    shadow = {
      enabled = false,
    },
    blur = {
      enabled = false,
      special = false,
    },
  },

  animations = {
    enabled = false,
  },

  render = {
    direct_scanout = 1,
  },
})

-- Mantener opacidad al 100% para máxima fluidez de la GPU en 2 monitores
o.window(".*", { tag = "-default-opacity", opacity = "1.0 1.0" })
o.window({ tag = "chromium-based-browser" }, { opacity = "1.0 1.0" })
o.window({ tag = "firefox-based-browser" }, { opacity = "1.0 1.0" })
o.window({ tag = "terminal" }, { opacity = "1.0 1.0" })

-- =============================================================================
-- Reglas de Ventanas Flotantes Híbridas (Estilo HyDE)
-- =============================================================================
-- Gestor de archivos siempre flotante y centrado
o.window("^(org.gnome.Nautilus|nautilus|org.kde.dolphin|thunar)$", { float = true, center = true, size = { 1000, 650 } })

-- Diálogos y utilidades del sistema
o.window("^(pavucontrol|org.pulseaudio.pavucontrol|blueman-manager|nm-connection-editor|org.gnome.Calculator|qalculate-gtk)$", { float = true, center = true, size = { 750, 520 } })

-- Visores multimedia
o.window("^(imv|eog|org.gnome.Loupe|mpv|vlc)$", { float = true, center = true, size = { 960, 600 } })

-- Regla de capa para el widget de calendario emergente (Wayland Layer Shell)
hl.layer_rule({ match = { namespace = "omarchy-calendar-popup" }, no_anim = true })
