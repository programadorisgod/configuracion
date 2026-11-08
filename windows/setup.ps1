# ==============================================================================
# Script de Despliegue de Configuracion para Windows
# ==============================================================================
# Instala y enlaza las configuraciones de Alacritty y Zellij en %APPDATA%
param(
    [switch]$InstallPackages
)

$ErrorActionPreference = "Stop"

# Refrescar PATH de Machine y User en la sesion actual
$env:PATH = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

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

# Verificacion e instalacion de paquetes
Write-Host "==> Verificando aplicaciones de terminal..." -ForegroundColor Cyan

$hasAlacritty = [bool](Get-Command alacritty -ErrorAction SilentlyContinue) -or (Test-Path "C:\Program Files\Alacritty\alacritty.exe")
$hasZellij = [bool](Get-Command zellij -ErrorAction SilentlyContinue) -or (Test-Path "$env:LOCALAPPDATA\Zellij\zellij.exe")

if (-not $hasAlacritty) {
    if ($InstallPackages) {
        Write-Host "    Instalando Alacritty mediante winget..." -ForegroundColor Yellow
        winget install --id Alacritty.Alacritty -e --accept-source-agreements --accept-package-agreements --silent
    } else {
        Write-Host "    [AVISO] Alacritty no detectado. Puedes instalarlo con:" -ForegroundColor Yellow
        Write-Host "            winget install Alacritty.Alacritty" -ForegroundColor Yellow
    }
} else {
    Write-Host "    [OK] Alacritty detectado e instalado." -ForegroundColor Green
}

if (-not $hasZellij) {
    if ($InstallPackages) {
        Write-Host "    Instalando Zellij mediante winget..." -ForegroundColor Yellow
        winget install --id Zellij.Zellij -e --accept-source-agreements --accept-package-agreements --silent
    } else {
        Write-Host "    [AVISO] Zellij no detectado. Puedes instalarlo con:" -ForegroundColor Yellow
        Write-Host "            winget install Zellij.Zellij" -ForegroundColor Yellow
    }
} else {
    Write-Host "    [OK] Zellij detectado e instalado." -ForegroundColor Green
}

Write-Host "`n==> Despliegue finalizado con exito." -ForegroundColor Green
