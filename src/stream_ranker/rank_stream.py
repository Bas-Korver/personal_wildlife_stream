import pathlib
import platform
import signal
import threading

import picologging

from core.config import settings
from db.redis_connection import RedisConnection
from modules.stream_score import stream_score
from redis.commands.json.path import Path


r = RedisConnection().get_redis_client()
picologging.basicConfig(level=settings.PROGRAM_LOG_LEVEL)
event = threading.Event()


class StreamRanking:
    def __init__(self, event):
        self.event = event

    def run(self):
        while True:
            if self.event.is_set():
                return

            # Get queue element
            try:
                video_path = pathlib.Path(r.brpop("queue:video_ranking", 10)[1])
            except TypeError:
                continue

            # Get directory and filename.
            filename = video_path.stem
            youtube_id = video_path.parent.name

            # Load video data from redis.
            data = r.json().get(f"video_information:{youtube_id}:{filename}")

            # Check if stream has image and audio detection results.
            if data["image_detection"] is None or data["audio_detection"] is None:
                continue

            # Save stream ranking.
            data["score"] = stream_score(
                data["image_detection"], data["audio_detection"]
            )

            # Save results.
            r.json().set(
                f"video_information:{youtube_id}:{filename}", Path.root_path(), data
            )


def handler(signum, frame):
    picologging.info(f"Interrupted by {signum}, shutting down")
    event.set()


if __name__ == "__main__":
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    detection = StreamRanking(event)
    detection.run()

    picologging.info("Started image detection.")