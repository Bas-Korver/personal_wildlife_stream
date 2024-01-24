import threading

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
            video = r.brpop("queue:not_finished_video")[1]
            # Wait for the length that FFmpeg will record one segment.
            self.event.wait(settings.VIDEO_SEGMENT_TIME)
            # Add video to queue for the data extraction.
            r.lpush("queue:video_data_extractor", video)
