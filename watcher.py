import time
import threading
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import agent
import notifier

DOWNLOADS = str(Path.home() / "Downloads")
STABLE_WAIT = 2.0
POLL_INTERVAL = 0.5
TEMP_EXTENSIONS = {".crdownload", ".part", ".tmp", ".download"}

logging.basicConfig(
    filename=str(Path(__file__).parent / "organizer.log"),
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)

_processing = set()
_lock = threading.Lock()


def _wait_until_stable(path: str) -> bool:
    prev_size = -1
    stable_for = 0.0
    while stable_for < STABLE_WAIT:
        try:
            size = Path(path).stat().st_size
        except FileNotFoundError:
            return False
        if size == prev_size:
            stable_for += POLL_INTERVAL
        else:
            stable_for = 0.0
            prev_size = size
        time.sleep(POLL_INTERVAL)
    return True


def _process(file_path: str):
    if Path(file_path).suffix.lower() in TEMP_EXTENSIONS:
        logging.debug(f"Skipping temp file: {file_path}")
        return
    with _lock:
        if file_path in _processing:
            return
        _processing.add(file_path)
    try:
        logging.info(f"Processing: {file_path}")
        if not _wait_until_stable(file_path):
            logging.warning(f"File disappeared: {file_path}")
            return
        result = agent.run(file_path)
        if result is None:
            logging.warning(f"Agent returned no suggestion for: {file_path}")
            return
        destination, reason = result
        logging.info(f"Suggestion: {destination} — {reason}")
        notifier.confirm_and_move(file_path, destination, reason)
    except Exception as e:
        logging.exception(f"Error processing {file_path}: {e}")
    finally:
        with _lock:
            _processing.discard(file_path)


class DownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            logging.debug(f"on_created: {event.src_path}")
            threading.Thread(target=_process, args=(event.src_path,), daemon=True).start()

    def on_moved(self, event):
        # Browsers rename .crdownload/.part to the final filename when download completes
        if not event.is_directory:
            logging.debug(f"on_moved: {event.src_path} -> {event.dest_path}")
            threading.Thread(target=_process, args=(event.dest_path,), daemon=True).start()


def start():
    logging.info("File organizer started, watching: " + DOWNLOADS)
    handler = DownloadHandler()
    observer = Observer()
    observer.schedule(handler, DOWNLOADS, recursive=False)
    observer.start()
    return observer
