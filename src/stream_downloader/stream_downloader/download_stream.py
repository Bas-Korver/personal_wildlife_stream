import platform
import shutil
import signal
import threading
from threading import Event

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

# TODO: Make this an API call.
YOUTUBE_URLS = [
    # "https://youtu.be/DsNtwGJXTTs",
    # "https://youtu.be/Ihr_nwydXi0",
    # "https://youtu.be/og8bbxl0iW8",
    # "https://youtu.be/4ElanH9Gzjw",
    "https://youtu.be/9pmsuKWKf90",
    # "https://youtu.be/LTz8tav2SCw",
    # "https://youtu.be/IVmL3diwJuw",
    # "https://youtu.be/StGk_2DA5ig",
    # "https://youtu.be/VUJbDTIYlM4",
    # "https://youtu.be/3MlJEXOZTfo",
    # "https://youtu.be/_NXaovxB-Bk",
    # "https://youtu.be/yfSyjwY6zSQ",
    # "https://youtu.be/KyQAB-TKOVA",
    # "https://youtu.be/O8xVFhgEv6Q",
    # "https://youtu.be/xWygD7kHTbY",
    # "https://youtu.be/yPSYdCWRWFA",
    # "https://youtu.be/jzx_n25g3kA",
    # "https://youtu.be/Kf-x20Yq0_A",
    # "https://youtu.be/Zern27X95Hg",
    # "https://youtu.be/T-iBupPtIFw",
    # "https://youtu.be/ydYDqZQpim8",
    # "https://youtu.be/E8ecY79xDME",
    # "https://youtu.be/kvEiF-TGXOQ",
    # "https://youtu.be/OMlf71t2oV0",
    # "https://youtu.be/-vK6dVJ7erU",
    # "https://youtu.be/VfFfS64rtZE",
    # "https://youtu.be/39uYW98qOV0",
    # "https://youtu.be/cKe0WSZKYgQ",
    # "https://youtu.be/Cq2qCph6Lx8",
    # "https://youtu.be/tn2LAEtFNbo",
    # "https://youtu.be/S4GIPXZnQTM",
    # "https://youtu.be/eZysNmy7dWI",
    # "https://youtu.be/I113nq5PmK4",
    # "https://youtu.be/wF_ytZyrW3w",
    # "https://youtu.be/ZFuWYnuu9I8",
    # "https://youtu.be/ItdXaWUVF48",
    # "https://youtu.be/5e4lsEe4Vew",
    # "https://youtu.be/pZZst4BOpVI",
    # "https://youtu.be/1zcIUk66HX4",
    # "https://youtu.be/Sq-X4Ga1oyc",
    # "https://youtu.be/QkWGGhtTA4k",
    # "https://youtu.be/Lv9t0hZTvz4",
    # "https://youtu.be/2swy9gysvOY",
    # "https://youtu.be/DRxYSIoBusQ",
    # "https://youtu.be/fvDXyApZjzo",
    # "https://youtu.be/OsH_Z88b1UU",
    # "https://youtu.be/7l2JMZRjgdU",
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
