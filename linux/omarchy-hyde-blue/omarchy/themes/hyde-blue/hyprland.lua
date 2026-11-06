local active_border_color = { colors = { "rgba(28b6f6ee)", "rgba(00e5ffee)" }, angle = 45 }
local inactive_border_color = "rgba(29354daa)"

hl.config({
  general = {
    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },
})
