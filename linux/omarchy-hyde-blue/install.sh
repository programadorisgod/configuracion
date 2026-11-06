#!/usr/bin/env bash
set -e

# Installer script for Omarchy Hyde Blue custom dotfiles
CONFIG_DIR="$HOME/.config"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Instalando configuración Hyde Blue en ~/.config ..."

# Crear directorios destino si no existen
mkdir -p "$CONFIG_DIR/hypr" \
         "$CONFIG_DIR/waybar/scripts" \
         "$CONFIG_DIR/omarchy/themes/hyde-blue/backgrounds" \
         "$CONFIG_DIR/walker/themes/hyde-blue" \
         "$CONFIG_DIR/swayosd" \
         "$CONFIG_DIR/systemd/user"

# Copiar archivos
cp -r "$BASE_DIR/hypr/"* "$CONFIG_DIR/hypr/"
cp -r "$BASE_DIR/waybar/"* "$CONFIG_DIR/waybar/"
chmod +x "$CONFIG_DIR/waybar/scripts/calendar-popup.py"

cp -r "$BASE_DIR/omarchy/themes/hyde-blue/"* "$CONFIG_DIR/omarchy/themes/hyde-blue/"
cp -r "$BASE_DIR/walker/"* "$CONFIG_DIR/walker/"
cp -r "$BASE_DIR/swayosd/"* "$CONFIG_DIR/swayosd/"
cp -r "$BASE_DIR/systemd/user/"* "$CONFIG_DIR/systemd/user/"

# Asegurar eliminación de toggle conflictivo si existiese
rm -f "$HOME/.local/state/omarchy/toggles/hypr/window-no-gaps.lua"

# Activar timer de rotación diaria
systemctl --user daemon-reload
systemctl --user enable --now daily-wallpaper.timer

# Aplicar tema
omarchy theme set "Hyde Blue"
hyprctl reload || true
omarchy restart waybar || true

echo "==> ¡Instalación completada con éxito!"
