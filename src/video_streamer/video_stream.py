import platform
import signal
import threading

import picologging

from core.config import settings
from db.redis_connection import RedisConnection
from modules.file_streamer import start_stream_file
from modules.streamer import start_stream
from modules.stream_selector import select_streams

r = RedisConnection().get_redis_client()
picologging.basicConfig(
    level=settings.PROGRAM_LOG_LEVEL,
    format="%(levelname)s - %(name)s - Line: %(lineno)d - Thread: %(thread)d - %(message)s",
)
event = threading.Event()
p_streamer = r.pubsub(ignore_subscribe_messages=True)
p_streamer.subscribe("streamer")


def start_threads():
    stream_selector_thread = threading.Thread(target=select_streams, args=(event,))
    file_streamer_thread = threading.Thread(target=start_stream_file, args=(event,))

    streamer_thread = threading.Thread(
        target=start_stream,
        args=(settings.STREAM_KEY.get_secret_value(), settings.FFMPEG_LOG_LEVEL),
    )

    picologging.debug("Starting stream selector thread.")
    stream_selector_thread.start()

    while True:
        if event.is_set():
            return

        data = p_streamer.get_message()
        if data is None:
            event.wait(3)
            continue

        picologging.debug(f"Received data from streamer: {data}")
        if data["data"] == "start_streaming":
            break

    picologging.info("Starting file streamer thread.")
    # file_streamer_thread.start()

    # Wait to start streamer, this will allow the file_streamer_thread to create a backlog.
    # event.wait(120)
    # TODO: Find a more resilient way to stream the stream.ts file and get the youtube live url.
    # streamer_thread.start()

    stream_selector_thread.join()
    # file_streamer_thread.join()
    # streamer_thread.join()


def handler(signum, frame):
    picologging.info(f"Interrupted by {signum}, shutting down")
    event.set()


if __name__ == "__main__":
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    start_threads()
