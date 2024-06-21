import os
import pathlib
from itertools import islice

from poetry.console.commands import self
from redis.commands.json.path import Path
from watchdog.events import FileSystemEventHandler

from db import RedisConnection
from modules import make_logger

logger = make_logger()

# Global variables
r = RedisConnection().get_redis_client()


class FileModifiedHandler(FileSystemEventHandler):
    def on_modified(self, event):
        path = pathlib.Path(event.src_path)
        if not event.is_directory and path.suffix == ".txt":
            logger.debug("Segment list file modified.", path=path)
            self.write_to_redis(path)

    @staticmethod
    def write_to_redis(segment_list_path: os.PathLike | str):
        segment_list_path = pathlib.Path(segment_list_path)
        stream_id = segment_list_path.parents[0].name
        stream_path = segment_list_path.parents[0]
        start = r.json().get("segment_list_information", f".{stream_id}")
        lines_read = 0

        with open(segment_list_path) as f:
            for file in islice(f, start, None):
                lines_read += 1
                video_path = pathlib.Path(f"{stream_path}/{file}")
                logger.debug("Writing segment to redis.", video_path=str(video_path))

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

                r.json().set(
                    f"video_information:{stream_id}:{video_path.stem}",
                    Path.root_path(),
                    data,
                )
                # Sometimes FFmpeg creates two video fragments at the same time, possibly due to a cache that FFmpeg
                # directly can download from YouTube. This is not wanted because the video_data_extractor could try to
                # open the same video twice While it's already removed.
                r.lrem("queue:video_data_extractor", 0, str(video_path))
                r.lpush(
                    "queue:video_data_extractor",
                    str(video_path),
                )
        r.json().set(
            "segment_list_information",
            f".{stream_id}",
            start + lines_read,
        )
