#!/usr/bin/env bash
# ==============================================================================
# Script de Aprovisionamiento para Linux (CachyOS / Arch) - OBS Pipeline
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_DIR}"

echo -e "\033[1;36m==> [1/5] Verificando dependencias del sistema en Linux...\033[0m"

# 1. Dependencias de sistema (Arch/CachyOS) incluyendo bubblewrap (bwrap) para la jaula de gflow
MISSING_PKGS=()
for pkg in uv ffmpeg bubblewrap; do
    if ! command -v "$pkg" &>/dev/null && ! pacman -Qi "$pkg" &>/dev/null; then
        MISSING_PKGS+=("$pkg")
    fi
done

# Driver VA-API i965 para Haswell Intel HD 4600
if ! pacman -Qi libva-intel-driver &>/dev/null; then
    MISSING_PKGS+=("libva-intel-driver")
fi

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    echo -e "\033[1;33m    Instalando paquetes faltantes: ${MISSING_PKGS[*]}...\033[0m"
    sudo pacman -S --needed --noconfirm "${MISSING_PKGS[@]}"
else
    echo -e "\033[1;32m    [OK] uv, FFmpeg, bubblewrap y libva-intel-driver ya están instalados.\033[0m"
fi

# 2. Verificar Antigravity CLI (agy)
if ! command -v agy &>/dev/null && [ ! -f "${HOME}/.local/bin/agy" ]; then
    echo -e "\033[1;33m    Instalando Antigravity CLI (agy)...\033[0m"
    curl -fsSL https://antigravity.google/cli/install.sh | bash
else
    echo -e "\033[1;32m    [OK] Antigravity CLI (agy) detectado.\033[0m"
fi

# 3. Sincronizar entorno virtual con uv (Python 3.12)
echo -e "\n\033[1;36m==> [2/5] Sincronizando entorno virtual (Python 3.12) y dependencias...\033[0m"
uv python pin 3.12
uv sync

# 4. Instalar gflow-cli versión fijada auditada (0.95.0)
echo -e "\n\033[1;36m==> [3/5] Instalando gflow-cli v0.95.0 (versión fijada por seguridad)...\033[0m"
uv tool install --python 3.12 "gflow-cli==0.95.0"
echo -e "\033[1;33m    Instalando Chromium de Playwright para gflow-cli...\033[0m"
uv tool run --python 3.12 --from "gflow-cli==0.95.0" playwright install chromium

# 5. Diagnóstico
echo -e "\n\033[1;36m==> [4/5] Ejecutando diagnóstico del entorno y blindaje...\033[0m"
uv run obs-pipe doctor

echo -e "\n\033[1;32m==> [5/5] ¡Aprovisionamiento en Linux completado con éxito!\033[0m"
echo -e "\033[1;36m    Para iniciar sesión en Google Flow dentro de la jaula aislada, ejecuta:\033[0m"
echo -e "\033[1;33m          uv run obs-pipe gflow-login\033[0m\n"
