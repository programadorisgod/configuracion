-- Modo Máximo Rendimiento para Intel Haswell (i5-4590S / HD 4600)
-- Aceleración por hardware para video y eliminación de sobrecarga gráfica

-- Forzar el driver VA-API correcto para Intel Gen 7.5 (Haswell)
hl.env("LIBVA_DRIVER_NAME", "i965")
hl.env("VDPAU_DRIVER", "va_gl")
hl.env("MOZ_DRM_DEVICE", "/dev/dri/renderD128")

hl.config({
  decoration = {
    rounding = 0,
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

-- Desactivar opacidad/transparencia forzada para permitir Direct Scanout y reducir uso de GPU en 2 monitores
o.window(".*", { tag = "-default-opacity", opacity = "1.0 1.0" })
o.window({ tag = "chromium-based-browser" }, { opacity = "1.0 1.0" })
o.window({ tag = "firefox-based-browser" }, { opacity = "1.0 1.0" })
o.window({ tag = "terminal" }, { opacity = "1.0 1.0" })
