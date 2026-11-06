-- =============================================================================
-- Atajos de Aplicaciones Limpios y Personalizados
-- =============================================================================

-- Aplicaciones Esenciales del Sistema
o.bind("SUPER + RETURN", "Terminal", { omarchy = "terminal" })
o.bind("SUPER + ALT + RETURN", "Terminal (Flotante)", "omarchy-launch-floating-terminal-with-presentation bash")
o.bind("SUPER + SHIFT + RETURN", "Browser", { omarchy = "browser" })
o.bind("SUPER + SHIFT + B", "Browser", { omarchy = "browser" })
o.bind("SUPER + SHIFT + ALT + B", "Browser (private)", { omarchy = "browser --private" })
o.bind("SUPER + SHIFT + F", "File manager", { omarchy = "nautilus" })
o.bind("SUPER + ALT + SHIFT + F", "File manager (cwd)", { omarchy = "nautilus-cwd" })
o.bind("SUPER + SHIFT + N", "Editor", { omarchy = "editor" })

-- Atajos Web directos a pestañas en Zen Browser (sin error de Chrome)
o.bind("SUPER + SHIFT + Y", "YouTube", "omarchy-launch-browser https://youtube.com")
o.bind("SUPER + SHIFT + A", "ChatGPT", "omarchy-launch-browser https://chatgpt.com")
