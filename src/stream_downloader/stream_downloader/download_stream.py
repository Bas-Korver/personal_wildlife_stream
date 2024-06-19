import platform
import shutil
import signal
import threading
from threading import Event

import requests
from watchdog.observers import Observer

from core import settings
from db import RedisConnection
from modules import DownloadThread
from modules import FileCreatedHandler
from modules import QueueHandler
from modules import make_logger

r = RedisConnection().get_redis_client()
event = Event()
logger = make_logger()


def start_download_threads():
    threads = []

    # TODO make configurable
    streams = requests.get("http://localhost:8003/v1/internal-streams/streams").json()

    # TODO: make it configurable that the stream will only download an n number of streams at the same time and
    #  alternate between active and inactive streams every x amount of time.
    # Create a download thread for each stream.
    for stream in streams:
        thread = DownloadThread(stream["id"], stream["url"], event)
        threads.append(thread)

    # Start all threads.
    for thread in threads:
        thread.start()

    logger.info("Started all threads for stream downloading.")
    logger.debug("Thread names", threads=threads)

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
    for _ in range(2):
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
        "Received a stop signal, shutting down and cleaning up. Do not force quit, because this will impede the cleanup process."
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
