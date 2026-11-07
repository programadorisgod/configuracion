#!/usr/bin/env bash
# Wrapper de ejecución rápida para Linux
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_DIR}"
exec uv run obs-pipe "$@"
