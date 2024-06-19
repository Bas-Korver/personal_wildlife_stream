import os
import pathlib
from watchdog.events import FileSystemEventHandler

from db import RedisConnection

# Global variables
r = RedisConnection().get_redis_client()


class FileCreatedHandler(FileSystemEventHandler):
    def on_created(self, event):
        print(event)
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
        r.lpush("queue:not_finished_video", str(path))
