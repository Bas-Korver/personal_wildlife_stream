import platform
import shutil
import signal
import threading
from threading import Event

import picologging
import structlog
import colorama
from watchdog.observers import Observer

from core.config import settings
from db.redis_connection import RedisConnection
from modules.downloader import DownloadThread
from modules.file_watcher import FileCreatedHandler
from modules.queue_handler import QueueHandler

# Global variables
r = RedisConnection().get_redis_client()
picologging.basicConfig(
    level=settings.PROGRAM_LOG_LEVEL,
    format="%(levelname)s - %(name)s - Line: %(lineno)d - Thread: %(threadName)s - %(message)s",
)
logger = picologging.getLogger("download_stream")
event = Event()

# TODO: Make this an API call.
YOUTUBE_URLS = [
    "https://www.youtube.com/watch?v=yPSYdCWRWFA",
    "https://www.youtube.com/watch?v=DsNtwGJXTTs",
    "https://www.youtube.com/watch?v=O52zDyxg5QI",
    "https://www.youtube.com/watch?v=wF_ytZyrW3w",
    "https://www.youtube.com/watch?v=k9Jlhqu_a_Q",
    "https://www.youtube.com/watch?v=Lf5t_JJTO00",
    "https://www.youtube.com/watch?v=yfSyjwY6zSQ",
    "https://www.youtube.com/watch?v=ZFuWYnuu9I8",
    "https://www.youtube.com/watch?v=VUJbDTIYlM4",
    "https://www.youtube.com/watch?v=5e4lsEe4Vew",
]


def start_download_threads():
    threads = []

    # Create a download thread for each YouTube URL.
    for youtube_url in YOUTUBE_URLS:
        thread = DownloadThread(youtube_url, event)
        threads.append(thread)

    # Start all threads.
    for thread in threads:
        thread.start()

    logger.info("Started all threads for stream download.")

    # Wait for all threads to finish and join them.
    for thread in threads:
        while thread.is_alive():
            thread.join(1)


def start_file_watcher():
    # Load event handler and create observer to watch for file changes.
    event_handler = FileCreatedHandler()
    observer = Observer()
    observer.schedule(event_handler, settings.SAVE_PATH, recursive=True)
    observer.start()

    logger.info("Started file watcher.")


def start_queue_handler():
    threads = []

    # Create a queue handler thread for each YouTube URL.
    for _ in YOUTUBE_URLS:
        thread = QueueHandler(event)
        threads.append(thread)

    for thread in threads:
        thread.start()

    logger.info("Started queue handler.")


def cleanup():
    logger.info("Cleaning up. Deleting all downloaded files and cleaning up redis.")

    # Wait for all threads to finish.
    while threading.active_count() > 1:
        # Wait for at least the download threads to finish otherwise errors will occur when deleting the files.
        if "DownloadThread" not in str(threading.enumerate()):
            break

    for item in settings.SAVE_PATH.iterdir():
        if item.is_dir():
            shutil.rmtree(item)

    # Delete all keys in redis.
    # TODO: add suffix to all keys for easier deletion
    for key in r.scan_iter("queue:*"):
        r.delete(key)

    for key in r.scan_iter("video_information:*"):
        r.delete(key)

    r.delete("stream_information")
    r.delete("stream_order")


def handler(signum, frame):
    logger.info(
        "Received a stop signal, shutting down and cleaning up.\nDo not force quit, because this will impede the cleanup process."
    )
    logger.debug(f"Interrupted by {signum}, shutting down")
    event.set()
    cleanup()


if __name__ == "__main__":
    # Register signal handlers.
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    # Call the functions to start the different threads.
    start_file_watcher()
    start_queue_handler()
    start_download_threads()
