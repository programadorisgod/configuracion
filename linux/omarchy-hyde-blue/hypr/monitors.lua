-- See https://wiki.hypr.land/Configuring/Basics/Monitors/

local omarchy_gdk_scale = 1

hl.env("GDK_SCALE", tostring(omarchy_gdk_scale))

-- Monitor principal
hl.monitor({
	output = "DP-1",
	mode = "preferred",
	position ="0x0",
})
