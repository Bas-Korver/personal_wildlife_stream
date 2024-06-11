import pathlib
import platform
import signal
import threading
import time

import structlog

from core.config import settings
from db.redis_connection import (
    RedisConnection,
)
from modules.audio_extractor import (
    extract_audio,
)
from modules.frame_extractor import (
    get_frames_from_video,
)

# Global variables
r = RedisConnection().get_redis_client()
structlog.stdlib.recreate_defaults(log_level=settings.PROGRAM_LOG_LEVEL)
logger = structlog.get_logger()
event = threading.Event()
lock = threading.Lock()


class DataExtractor(threading.Thread):
    def __init__(self, event):
        super().__init__()
        self.event = event

    def run(self):
        while True:
            if self.event.is_set():
                return

            # Get queue element
            try:
                video_path = pathlib.Path(r.brpop("queue:video_data_extractor", 10)[1])
            except TypeError:
                logger.debug(f"Queue is empty, retrying")
                continue

            # Save start time.
            start_time = time.time()

            # Get directory and filename.
            filename = video_path.stem
            youtube_id = video_path.parent.name

            logger.debug(
                f"Video_data_extractor: Got video {youtube_id}_{filename} from queue"
            )

            # Extract frames from video
            successful = get_frames_from_video(
                event, video_path, settings.FRAMES_PER_SECOND, settings.FRAMES_TO_GET
            )

            if not successful:
                logger.error(f"Failed to extract frames from {video_path}")
                # TODO: add frames cleanup
                continue

            # Extract audio from video
            extract_audio(video_path)

            # Save processing time.
            r.json().set(
                f"video_information:{youtube_id}:{video_path.stem}",
                ".processing_times.data_extractor",
                time.time() - start_time,
            )

            # Add video to the queue for level 1 detection
            r.lpush("queue:level_1_detection_motion", str(video_path))
            r.lpush("queue:audio_detection", str(video_path))


def handler(signum, frame):
    logger.info(f"Interrupted by {signum}, shutting down")
    event.set()  # TODO: add intermediate.ts file cleanup


if __name__ == "__main__":
    # Register signal handlers
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    # Start threads
    threads = []
    for _ in range(settings.THREAD_COUNT):
        threads.append(DataExtractor(event))

    for thread in threads:
        thread.start()

    logger.info("Started all threads for video extraction.")

    for thread in threads:
        while thread.is_alive():
            thread.join(1)
