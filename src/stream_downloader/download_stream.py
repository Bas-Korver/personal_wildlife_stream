import platform
import shutil
import signal
import threading
from threading import Event

import picologging
from watchdog.observers import Observer

from core.config import settings
from db.redis_connection import RedisConnection
from downloader import DownloadThread
from file_watcher import FileCreatedHandler

r = RedisConnection().get_redis_client()
picologging.basicConfig(level=settings.DOWNLOADER_LOG_LEVEL)
event = Event()

# TODO: Make this an api call.
YOUTUBE_URLS = [
    "https://www.youtube.com/watch?v=Ihr_nwydXi0",
    "https://www.youtube.com/watch?v=yPSYdCWRWFA",
]


def start_download_threads():
    threads = []
    for youtube_url in YOUTUBE_URLS:
        thread = DownloadThread(youtube_url, event)
        threads.append(thread)

    for thread in threads:
        thread.start()

    picologging.info("Started all threads for stream download.")

    for thread in threads:
        while thread.is_alive():
            thread.join(1)


def start_file_watcher():
    event_handler = FileCreatedHandler()
    observer = Observer()
    observer.schedule(event_handler, settings.SAVE_PATH, recursive=True)
    observer.start()


def cleanup():
    picologging.info(
        "Cleaning up. Deleting all downloaded files and cleaning up redis."
    )

    while threading.active_count() > 1:
        if "DownloadThread" not in str(threading.enumerate()):
            break

    for item in settings.SAVE_PATH.iterdir():
        shutil.rmtree(item)

    for key in r.scan_iter("queue:*"):
        r.delete(key)
    event.set()


def handler(signum, frame):
    picologging.info(f"Interrupted by {signum}, shutting down")
    event.set()
    cleanup()


if __name__ == "__main__":
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    start_file_watcher()

    start_download_threads()
