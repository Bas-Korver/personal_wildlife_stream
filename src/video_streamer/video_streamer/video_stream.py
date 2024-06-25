import platform
import signal
import threading
import time

from core import settings
from db import RedisConnection
from modules import start_stream_file, select_streams, start_stream, make_logger

r = RedisConnection().get_redis_client()
event = threading.Event()
logger = make_logger()
p_streamer = r.pubsub(ignore_subscribe_messages=True)
p_streamer.subscribe("streamer")


class ServiceExit(Exception):
    pass


def start_threads(threads):
    threads.extend(
        [
            threading.Thread(
                target=select_streams,
                args=(event,),
            ),
            threading.Thread(
                target=start_stream_file,
                args=(event,),
            ),
            # TODO fix streaming
            threading.Thread(
                target=start_stream,
                args=(
                    settings.STREAM_KEY.get_secret_value(),
                    settings.FFMPEG_LOG_LEVEL,
                ),
            ),
        ]
    )

    logger.debug("Starting stream selector thread.")
    threads[0].start()

    while True:
        if event.is_set():
            return

        data = p_streamer.get_message()
        if data is None:
            event.wait(3)
            continue

        logger.debug(f"Received data from file streamer", data=data)
        if data["data"] == "start_streaming":
            break

    logger.info("Starting file streamer thread.")
    threads[1].start()

    # Wait to start streamer, this will allow the file_streamer_thread to create a backlog.
    event.wait(300)
    # TODO: Find a more resilient way to stream the stream.ts file and get the youtube live url.
    threads[2].start()

    return threads


def handler(signum, frame):
    logger.info("Received a stop signal, shutting down")
    logger.debug("Interrupted by:", signum=signum, signame=signal.Signals(signum).name)
    raise ServiceExit


if __name__ == "__main__":
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    threads = []

    try:
        threads = start_threads(threads)
        logger.info("Started streamer")

        while True:
            time.sleep(0.5)
    except ServiceExit:
        event.set()
        for thread in threads:
            thread.join()
        logger.info("Stopped streamer")
