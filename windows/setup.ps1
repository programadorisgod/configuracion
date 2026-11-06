# ==============================================================================
# Script de Despliegue de Configuración para Windows
# ==============================================================================
# Instala y enlaza las configuraciones de Alacritty y Zellij en %APPDATA%

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$AlacrittyTargetDir = "$env:APPDATA\alacritty"
$ZellijTargetDir = "$env:APPDATA\Zellij\config"

Write-Host "==> Configurando Alacritty..." -ForegroundColor Cyan
if (-not (Test-Path $AlacrittyTargetDir)) {
    New-Item -ItemType Directory -Path $AlacrittyTargetDir -Force | Out-Null
}
Copy-Item "$ScriptDir\terminal\alacritty\alacritty.toml" "$AlacrittyTargetDir\alacritty.toml" -Force
Write-Host "    [OK] alacritty.toml instalado en $AlacrittyTargetDir" -ForegroundColor Green

Write-Host "==> Configurando Zellij..." -ForegroundColor Cyan
if (-not (Test-Path $ZellijTargetDir)) {
    New-Item -ItemType Directory -Path $ZellijTargetDir -Force | Out-Null
}
Copy-Item "$ScriptDir\terminal\zellij\config.kdl" "$ZellijTargetDir\config.kdl" -Force
Write-Host "    [OK] config.kdl instalado en $ZellijTargetDir" -ForegroundColor Green

# Verificación de binarios
Write-Host "==> Verificando aplicaciones instaladas..." -ForegroundColor Cyan
if (-not (Get-Command alacritty -ErrorAction SilentlyContinue)) {
    Write-Host "    [AVISO] Alacritty no se encuentra en el PATH. Puedes instalarlo con:" -ForegroundColor Yellow
    Write-Host "            winget install Alacritty.Alacritty" -ForegroundColor Yellow
} else {
    Write-Host "    [OK] Alacritty detectado." -ForegroundColor Green
}

if (-not (Get-Command zellij -ErrorAction SilentlyContinue)) {
    Write-Host "    [AVISO] Zellij no se encuentra en el PATH. Puedes instalarlo con:" -ForegroundColor Yellow
    Write-Host "            winget install Zellij.Zellij" -ForegroundColor Yellow
} else {
    Write-Host "    [OK] Zellij detectado." -ForegroundColor Green
}

Write-Host "`n==> Despliegue finalizado con éxito." -ForegroundColor Green
