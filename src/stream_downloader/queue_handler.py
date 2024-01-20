import threading

from db.redis_connection import RedisConnection
from core.config import settings

r = RedisConnection().get_redis_client()


class QueueHandler(threading.Thread):
    def __init__(self, event):
        super().__init__()
        self.event = event

    def run(self):
        while not self.event.is_set():
            video = r.brpop("queue:not_finished_video")[1]
            self.event.wait(settings.VIDEO_SEGMENT_TIME)
            r.lrem("queue:video_data_extractor", 0, video)
            r.lpush("queue:video_data_extractor", video)
