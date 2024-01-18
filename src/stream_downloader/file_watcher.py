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
            self.write_to_redis(pathlib.Path(event.src_path))

    @staticmethod
    def write_to_redis(path: pathlib.Path):
        r.lrem("queue:video_data_extractor", 0, str(path))
        r.lpush("queue:video_data_extractor", str(path))


if __name__ == "__main__":
    path = "./streams"
    event_handler = FileCreatedHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()
