import threading
import time
import sys

import schedule

import graph_semantic
import watcher


def _run_scheduler() -> None:
    schedule.every().day.at("02:00").do(graph_semantic.refresh)
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    threading.Thread(target=_run_scheduler, daemon=True).start()
    observer = watcher.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    sys.exit(0)
