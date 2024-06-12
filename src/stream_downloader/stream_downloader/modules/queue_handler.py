import pathlib
import threading
from redis.commands.json.path import Path

from core.config import settings
from db.redis_connection import RedisConnection

# Global variables
r = RedisConnection().get_redis_client()


class QueueHandler(threading.Thread):
    def __init__(self, event):
        super().__init__()
        self.event = event

    def run(self):
        while not self.event.is_set():
            # Get video from queue.
            video_path = pathlib.Path(r.brpop("queue:not_finished_video")[1])

            # Wait for the length that FFmpeg will record one segment.
            self.event.wait(settings.VIDEO_SEGMENT_TIME)

            data = {
                "video_path": str(video_path),
                "motion": None,
                "image_detection": None,
                "audio_detection": None,
                "score": None,
                "processing_times": {
                    "data_extractor": None,
                    "motion_detection": None,
                    "audio_detection": None,
                    "image_detection": None,
                    "ranker": None,
                },
            }

            youtube_id = video_path.parent.name

            # Save results.
            r.json().set(
                f"video_information:{youtube_id}:{video_path.stem}",
                Path.root_path(),
                data,
            )

            # Add video to queue for the data extraction.
            r.lpush("queue:video_data_extractor", str(video_path))
