"""
Capa de Blindaje de Seguridad (5 Capas) para ejecución de herramientas externas (gflow-cli).
Protege contra ataques de cadena de suministro (supply-chain), lectura de cookies del navegador
principal (browser-cookie3 / shadowcopy), telemetría no deseada y gasto accidental de créditos.
"""

import os
import shutil
import subprocess
from pathlib import Path
from obs_pipeline.hardware import is_windows, is_linux, find_binary


PINNED_GFLOW_VERSION = "0.95.0"

# Lista blanca estricta de subcomandos permitidos en gflow (bloquea 'video' que gasta créditos y 'update')
ALLOWED_GFLOW_SUBCOMMANDS = {
    ("auth", "status"),
    ("auth", "login"),
    ("auth", "list"),
    ("image", "t2i"),
}

# Variables de entorno sensibles que jamás deben filtrarse al subproceso de gflow
SENSITIVE_ENV_PREFIXES = (
    "GITHUB_",
    "GH_",
    "AWS_",
    "AZURE_",
    "GCP_",
    "SSH_",
    "ANTIGRAVITY_",
    "OPENAI_",
    "ANTHROPIC_",
    "STRIPE_",
)


class GFlowSecurityError(RuntimeError):
    """Excepción lanzada cuando un comando viola las políticas de seguridad de gflow."""


def get_gflow_jail_dir() -> Path:
    """Devuelve el directorio jaula (sandbox) aislado para el perfil de gflow-cli."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    jail_dir = repo_root / ".jail" / "gflow_home"
    (jail_dir / "AppData" / "Local").mkdir(parents=True, exist_ok=True)
    (jail_dir / "AppData" / "Roaming").mkdir(parents=True, exist_ok=True)
    (jail_dir / ".config").mkdir(parents=True, exist_ok=True)
    (jail_dir / ".local" / "share").mkdir(parents=True, exist_ok=True)
    return jail_dir


def build_sanitized_gflow_env(output_dir: Path | None = None) -> dict[str, str]:
    """
    Construye un entorno de variables limpio para gflow:
    1. Elimina tokens y credenciales del sistema.
    2. Redirige HOME / USERPROFILE / APPDATA a la jaula para que browser-cookie3
       no vea jamás los navegadores reales del usuario (Zen, Chrome personal, Edge).
    3. Fuerza desactivación de telemetría y redacción de historial.
    """
    clean_env: dict[str, str] = {}
    for k, v in os.environ.items():
        if any(k.upper().startswith(prefix) for prefix in SENSITIVE_ENV_PREFIXES):
            continue
        clean_env[k] = v

    jail_dir = get_gflow_jail_dir()

    # Preservar la ruta de los binarios de Playwright (Chromium) antes de redirigir LOCALAPPDATA
    real_home = Path.home()
    if is_windows():
        real_local_appdata = Path(os.environ.get("LOCALAPPDATA", str(real_home / "AppData" / "Local")))
        pw_browsers = real_local_appdata / "ms-playwright"
    else:
        pw_browsers = real_home / ".cache" / "ms-playwright"

    if pw_browsers.exists():
        clean_env["PLAYWRIGHT_BROWSERS_PATH"] = str(pw_browsers)

    # Redirigir directorios de usuario a la jaula aislada
    clean_env["HOME"] = str(jail_dir)
    clean_env["USERPROFILE"] = str(jail_dir)
    clean_env["APPDATA"] = str(jail_dir / "AppData" / "Roaming")
    clean_env["LOCALAPPDATA"] = str(jail_dir / "AppData" / "Local")
    clean_env["XDG_CONFIG_HOME"] = str(jail_dir / ".config")
    clean_env["XDG_DATA_HOME"] = str(jail_dir / ".local" / "share")

    # Blindaje anti-telemetría y privacidad
    clean_env["DO_NOT_TRACK"] = "1"
    clean_env["GFLOW_CLI_TELEMETRY"] = "0"
    clean_env["GFLOW_CLI_NO_TELEMETRY"] = "1"
    clean_env["GFLOW_CLI_HISTORY_PROMPTS"] = "redacted"

    if output_dir:
        clean_env["GFLOW_CLI_OUTPUT_DIR"] = str(output_dir)

    return clean_env


def validate_gflow_args(args: list[str]) -> None:
    """Verifica que los argumentos estén en la lista blanca y no gasten créditos ni actualicen sin control."""
    if len(args) < 2:
        raise GFlowSecurityError(f"Subcomando gflow inválido o incompleto: {args}")

    pair = (args[0], args[1])
    if pair not in ALLOWED_GFLOW_SUBCOMMANDS:
        raise GFlowSecurityError(
            f"Subcomando bloqueado por política de seguridad: 'gflow {' '.join(args[:2])}'. "
            f"Solo se permiten operaciones gratuitas de imagen y autenticación: {ALLOWED_GFLOW_SUBCOMMANDS}"
        )


def run_sandboxed_gflow(
    args: list[str],
    output_dir: Path | None = None,
    timeout: int = 120,
    interactive: bool = False,
) -> subprocess.CompletedProcess:
    """
    Ejecuta gflow-cli dentro de la jaula de seguridad multiplataforma (Windows & Linux).
    """
    validate_gflow_args(args)
    env = build_sanitized_gflow_env(output_dir)

    gflow_bin = find_binary("gflow")
    if shutil.which(gflow_bin) or Path(gflow_bin).exists():
        base_cmd = [gflow_bin]
    else:
        uv_bin = find_binary("uv")
        base_cmd = [uv_bin, "tool", "run", "--python", "3.12", "--from", f"gflow-cli=={PINNED_GFLOW_VERSION}", "gflow"]

    full_cmd = base_cmd + args

    # En Linux, si bwrap (Bubblewrap) está instalado, aplicamos aislamiento a nivel de kernel (mount namespace)
    if is_linux() and shutil.which("bwrap"):
        jail_dir = get_gflow_jail_dir()
        real_home = Path.home()
        bwrap_cmd = [
            "bwrap",
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind-try", "/lib64", "/lib64",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/etc", "/etc",
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp",
            "--tmpfs", str(real_home),
            "--bind", str(jail_dir), str(jail_dir),
            "--ro-bind-try", str(real_home / ".local"), str(real_home / ".local"),
            "--ro-bind-try", str(real_home / ".cache" / "ms-playwright"), str(real_home / ".cache" / "ms-playwright"),
        ]
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            bwrap_cmd.extend(["--bind", str(output_dir), str(output_dir)])
        full_cmd = bwrap_cmd + full_cmd

    if interactive:
        return subprocess.run(full_cmd, env=env, timeout=timeout, check=False)
    return subprocess.run(full_cmd, env=env, capture_output=True, text=True, timeout=timeout, check=False)
