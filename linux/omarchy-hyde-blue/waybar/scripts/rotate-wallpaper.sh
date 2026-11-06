#!/usr/bin/env bash
set -e

THEME_BG_DIR="$HOME/.config/omarchy/current/theme/backgrounds"
CURRENT_LINK="$HOME/.config/omarchy/current/background"

# Get all images sorted
mapfile -d '' -t BACKGROUNDS < <(
  find -L "$THEME_BG_DIR" -maxdepth 1 -type f \
    \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \) \
    -print0 | sort -z
)

TOTAL=${#BACKGROUNDS[@]}
if (( TOTAL == 0 )); then
  exit 0
fi

CURRENT_TARGET=""
if [[ -L "$CURRENT_LINK" ]]; then
  CURRENT_TARGET=$(readlink -f "$CURRENT_LINK")
fi

INDEX=-1
for i in "${!BACKGROUNDS[@]}"; do
  if [[ "${BACKGROUNDS[$i]}" == "$CURRENT_TARGET" ]]; then
    INDEX=$i
    break
  fi
done

NEXT_INDEX=$(((INDEX + 1) % TOTAL))
NEW_BG="${BACKGROUNDS[$NEXT_INDEX]}"

# Update symlink
ln -nsf "$NEW_BG" "$CURRENT_LINK"

# Restart swaybg cleanly via Hyprland
pkill -x swaybg 2>/dev/null || true
hyprctl eval "hl.exec_cmd('swaybg -i $HOME/.config/omarchy/current/background -m fill')" >/dev/null 2>&1
