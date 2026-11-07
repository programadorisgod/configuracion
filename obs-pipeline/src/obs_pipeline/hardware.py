import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_linux() -> bool:
    return platform.system() == "Linux"


def get_safe_threads(configured: int = 0) -> int:
    """Calcula el número óptimo de hilos de CPU para no congelar el sistema en CPUs de 4 hilos."""
    if configured > 0:
        return configured
    total = os.cpu_count() or 4
    return max(1, total - 1)


def find_binary(name: str) -> str:
    """Encuentra un ejecutable en el PATH o en ubicaciones estándar de Windows y Linux."""
    path = shutil.which(name)
    if path:
        return path

    home = Path.home()
    if is_windows():
        local_appdata = Path(os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local")))
        common_paths = [
            local_appdata / "agy" / "bin" / f"{name}.exe",
            home / ".local" / "bin" / f"{name}.exe",
            local_appdata / "Microsoft" / "WinGet" / "Links" / f"{name}.exe",
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / name / "bin" / f"{name}.exe",
        ]
        # Buscar en paquetes de WinGet si no está en Links
        winget_pkgs = local_appdata / "Microsoft" / "WinGet" / "Packages"
        if winget_pkgs.exists():
            for match in winget_pkgs.rglob(f"{name}.exe"):
                common_paths.append(match)
    else:
        common_paths = [
            home / ".local" / "bin" / name,
            Path("/usr/local/bin") / name,
            Path("/usr/bin") / name,
        ]

    for p in common_paths:
        if p.exists():
            return str(p)
    return name


def get_hw_video_encoder() -> tuple[str, list[str]]:
    """Detecta el codificador por hardware disponible para H.264 (si hiciera falta re-codificar)."""
    ffmpeg_bin = find_binary("ffmpeg")
    try:
        res = subprocess.run([ffmpeg_bin, "-encoders"], capture_output=True, text=True, check=True)
        out = res.stdout
    except Exception:
        out = ""

    if is_linux() and "h264_vaapi" in out:
        # En Linux Haswell i5-4590S / HD 4600 se usa driver i965
        os.environ.setdefault("LIBVA_DRIVER_NAME", "i965")
        return "h264_vaapi", ["-vaapi_device", "/dev/dri/renderD128", "-vf", "format=nv12,hwupload"]
    elif is_windows() and "h264_qsv" in out:
        return "h264_qsv", ["-load_plugin", "hevc_hw"]

    # Fallback software ultra-rápido de bajo impacto
    return "libx264", ["-preset", "veryfast", "-crf", "21"]


def send_desktop_notification(title: str, message: str) -> None:
    """Alias compatible para notificaciones de escritorio."""
    send_notification(title, message)


def send_notification(title: str, message: str) -> None:
    """Lanza una notificación nativa en el escritorio (Linux Hyprland / Windows)."""
    try:
        if is_linux():
            if shutil.which("notify-send"):
                subprocess.run(["notify-send", "-a", "OBS Pipeline", title, message], check=False)
        elif is_windows():
            ps_script = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            $template = @"
            <toast>
                <visual>
                    <binding template="ToastGeneric">
                        <text>{title}</text>
                        <text>{message}</text>
                    </binding>
                </visual>
            </toast>
"@
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("OBS Pipeline").Show($toast)
            """
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, check=False)
    except Exception:
        pass
