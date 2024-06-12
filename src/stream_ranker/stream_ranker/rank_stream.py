import pathlib
import platform
import signal
import structlog
import threading
import time

from core.config import settings
from db.redis_connection import RedisConnection
from modules.stream_score import stream_score

# Global variables
r = RedisConnection().get_redis_client()
structlog.stdlib.recreate_defaults(log_level=settings.PROGRAM_LOG_LEVEL)
logger = structlog.get_logger()
event = threading.Event()


class StreamRanking(threading.Thread):
    def __init__(self, event):
        super().__init__()
        self.event = event

    def run(self):
        while True:
            if self.event.is_set():
                return

            # Get queue element
            try:
                # TODO use LPOS
                video_path = pathlib.Path(r.brpop("queue:video_ranking", 10)[1])
            except TypeError:
                logger.debug(f"Queue is empty, retrying")
                continue

            # Save start time.
            start_time = time.time()

            # Get directory and filename.
            filename = video_path.stem
            youtube_id = video_path.parent.name

            # Load video data from redis.
            data = r.json().get(f"video_information:{youtube_id}:{filename}")

            # Check if stream has image and audio detection results.
            if data["image_detection"] is None or data["audio_detection"] is None:
                # TODO: add duplicate deletion.
                r.rpush("queue:video_ranking", str(video_path))
                continue

            # Save stream ranking.
            score = stream_score(
                youtube_id, data["image_detection"], data["audio_detection"]
            )

            # Save results.
            r.json().set(f"video_information:{youtube_id}:{filename}", ".score", score)

            # Save processing time.
            r.json().set(
                f"video_information:{youtube_id}:{video_path.stem}",
                ".processing_times.motion_detection",
                time.time() - start_time,
            )

            logger.debug(f"Saved stream ranking: {youtube_id}:{filename} {score=}")


def handler(signum, frame):
    logger.info(f"Interrupted by {signum}, shutting down")
    event.set()


if __name__ == "__main__":
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    thread = StreamRanking(event)
    thread.run()

    logger.info("Started stream ranking.")
