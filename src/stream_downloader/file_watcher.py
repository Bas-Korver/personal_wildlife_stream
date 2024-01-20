import os
import pathlib

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from db.redis_connection import RedisConnection

r = RedisConnection().get_redis_client()


class FileCreatedHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return None
        elif event.event_type == "created":
            # Take any action here when a file is first created.
            path = pathlib.Path(event.src_path)
            if path.suffix == ".mp4":
                self.write_to_redis(pathlib.Path(event.src_path))

    @staticmethod
    def write_to_redis(path: os.PathLike):
        path = pathlib.Path(path)
        r.lrem("queue:not_finished_video", 0, str(path))
        r.lpush("queue:not_finished_video", str(path))
