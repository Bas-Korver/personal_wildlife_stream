import platform
import shutil
import signal
import threading
import time

import requests
from redis.commands.json.path import Path
from watchdog.observers import Observer

from core import settings
from db import RedisConnection
from modules import DownloadThread, FileHandler, make_logger

r = RedisConnection().get_redis_client()
event = threading.Event()
logger = make_logger()


class ServiceExit(Exception):
    pass


def initialize_redis_json_key(key: str):
    if not r.exists(key):
        r.json().set(key, Path.root_path(), {})


def start_download_threads(threads):
    # TODO make endpoint configurable
    streams = requests.get(
        f"{settings.FULL_PRIVATE_API_URL}/v1/internal-streams/streams"
    ).json()

    # TODO: make it configurable that the stream will only download an n number of streams at the same time and
    #  alternate between active and inactive streams every x amount of time.
    # Create a download thread for each stream.
    i = 0
    for stream in streams:
        thread = DownloadThread(stream["id"], stream["url"], event)
        threads.append(thread)
        i += 1
        if i >= 20:
            break

    # Start all threads.
    for thread in threads:
        thread.start()

    logger.info("Started all threads for stream downloading.")
    logger.debug("Thread names", threads=threads)


def start_file_watcher(observer: Observer):
    # Load event handler and create observer to watch for file changes.
    event_handler = FileHandler()
    observer.schedule(event_handler, settings.SAVE_PATH, recursive=True)
    observer.start()

    logger.info("Started file watcher.")
    logger.debug("Observer name", observer=observer)


def cleanup():
    logger.info("Cleaning up. Deleting all downloaded files and cleaning up redis.")

    # Wait for all threads to finish.
    while threading.active_count() > 1:
        # Wait for at least the download threads to finish otherwise errors will occur when deleting the files.
        if "DownloadThread" not in str(threading.enumerate()):
            break

    # Delete all keys in redis.
    for key in r.scan_iter("queue:*"):
        r.delete(key)

    for key in r.scan_iter("video_information:*"):
        r.delete(key)

    r.delete("stream_information")
    r.delete("segment_list_information")
    r.delete("stream_order")

    for item in settings.SAVE_PATH.iterdir():
        if item.is_dir():
            shutil.rmtree(item)


def handler(signum, frame):
    logger.info(
        "Received a stop signal, shutting down and cleaning up. "
        "Do not force quit!!, since this will impede the cleanup process."
    )
    logger.debug("Interrupted by:", signum=signum, signame=signal.Signals(signum).name)
    raise ServiceExit


if __name__ == "__main__":
    # Register signal handlers.
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    # Create the observer and threads list.
    threads = []
    observer = Observer()

    # Initialize redis json keys for writing information to it.
    initialize_redis_json_key("stream_information")
    initialize_redis_json_key("segment_list_information")

    try:
        # Call the functions to start the different threads.
        start_file_watcher(observer)
        start_download_threads(threads)

        while True:
            time.sleep(0.5)
    except ServiceExit:
        event.set()
        for thread in threads:
            thread.join()
        observer.stop()
        observer.join()
        # Cleanup when the program is done.
        cleanup()
