# ==============================================================================
# Script de Aprovisionamiento para Windows - OBS Pipeline
# ==============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectDir = Split-Path -Parent $ScriptDir
Set-Location $ProjectDir

Write-Host "==> [1/5] Verificando dependencias del sistema en Windows..." -ForegroundColor Cyan

# 1. Verificar / Instalar uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "    Instalando uv mediante winget..." -ForegroundColor Yellow
    winget install --id=astral-sh.uv -e --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "    [OK] uv ya está instalado." -ForegroundColor Green
}

# 2. Verificar / Instalar FFmpeg
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "    Instalando FFmpeg mediante winget..." -ForegroundColor Yellow
    winget install --id=Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "    [OK] FFmpeg ya está instalado." -ForegroundColor Green
}

# 3. Verificar Antigravity CLI (agy)
$AgyPath = "$env:LOCALAPPDATA\agy\bin\agy.exe"
if (-not (Get-Command agy -ErrorAction SilentlyContinue) -and -not (Test-Path $AgyPath)) {
    Write-Host "    Instalando Antigravity CLI (agy)..." -ForegroundColor Yellow
    irm https://antigravity.google/cli/install.ps1 | iex
} else {
    Write-Host "    [OK] Antigravity CLI (agy) detectado." -ForegroundColor Green
}

# 4. Sincronizar entorno virtual de Python 3.12 con uv
Write-Host "`n==> [2/5] Sincronizando entorno virtual (Python 3.12) y dependencias..." -ForegroundColor Cyan
uv python pin 3.12
uv sync

# 5. Instalar gflow-cli versión fijada auditada (0.95.0)
Write-Host "`n==> [3/5] Instalando gflow-cli v0.95.0 (versión fijada por seguridad)..." -ForegroundColor Cyan
uv tool install --python 3.12 "gflow-cli==0.95.0"
Write-Host "    Instalando Chromium de Playwright para gflow-cli..." -ForegroundColor Yellow
uv tool run --python 3.12 --from "gflow-cli==0.95.0" playwright install chromium

# 6. Ejecutar diagnóstico
Write-Host "`n==> [4/5] Ejecutando diagnóstico del entorno y blindaje..." -ForegroundColor Cyan
uv run obs-pipe doctor

Write-Host "`n==> [5/5] ¡Aprovisionamiento completado con éxito!" -ForegroundColor Green
Write-Host "    Para iniciar sesión en Google Flow dentro de la jaula aislada, ejecuta:" -ForegroundColor Cyan
Write-Host "          uv run obs-pipe gflow-login`n" -ForegroundColor Yellow
