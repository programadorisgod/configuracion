# Wrapper de ejecución rápida para Windows
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectDir = Split-Path -Parent $ScriptDir
Set-Location $ProjectDir
uv run obs-pipe @args
