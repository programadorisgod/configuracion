import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger("obs_pipeline.watcher")


def wait_for_file_stabilization(file_path: Path, stable_seconds: int = 3) -> bool:
    """Espera a que OBS termine de escribir en el archivo y libere el bloqueo."""
    last_size = -1
    consecutive_matches = 0

    # Espera máxima de 2 minutos por si la grabación está finalizando
    for _ in range(120):
        try:
            if not file_path.exists():
                return False
            curr_size = file_path.stat().st_size
            if curr_size > 0 and curr_size == last_size:
                consecutive_matches += 1
                if consecutive_matches >= stable_seconds:
                    # Intento de apertura para verificar que OBS soltó el handle
                    with open(file_path, "rb"):
                        return True
            else:
                consecutive_matches = 0
            last_size = curr_size
        except (PermissionError, OSError):
            consecutive_matches = 0
        time.sleep(1.0)

    return False


class ObsRecordingHandler(FileSystemEventHandler):
    def __init__(self, processor_callback, extensions=(".mp4", ".mkv")):
        self.processor_callback = processor_callback
        self.extensions = extensions
        self.processed = set()

    def on_created(self, event):
        if event.is_directory:
            return
        p = Path(event.src_path)
        if p.suffix.lower() in self.extensions and not p.stem.endswith("_masterizado") and not p.stem.endswith("_audio_limpio"):
            if str(p) in self.processed:
                return
            logger.info("Detectada nueva grabación: %s. Esperando finalización de OBS...", p.name)
            if wait_for_file_stabilization(p):
                self.processed.add(str(p))
                logger.info("Grabación completada. Iniciando pipeline para %s", p.name)
                self.processor_callback(p)


def start_watching(directory: Path, processor_callback):
    """Inicia el vigilante de carpeta en segundo plano."""
    event_handler = ObsRecordingHandler(processor_callback)
    observer = Observer()
    observer.schedule(event_handler, str(directory), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
