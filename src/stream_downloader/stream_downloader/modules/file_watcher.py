import os
import pathlib
from itertools import islice

from redis.commands.json.path import Path
from watchdog.events import FileSystemEventHandler

from db import RedisConnection
from modules import make_logger

# Global variables
r = RedisConnection().get_redis_client()
logger = make_logger()


class FileHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        path = pathlib.Path(event.src_path)
        if not event.is_directory and path.suffix == ".txt":
            logger.debug(f"Segment list file {event.event_type}.", path=path)
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
                file = file.rstrip("\n")
                lines_read += 1
                video_file = pathlib.Path(f"{stream_path}/{file}")
                logger.debug("Writing segment to redis.", video_path=video_file)

                data = {
                    "video_path": str(video_file.as_posix()),
                    "video_duration": None,
                    "motion": None,
                    "audio_detection": None,
                    "image_detection": None,
                    "narration_subtitle": None,
                    "score": None,
                    "processing_times": {},
                }

                r.json().set(
                    f"video_information:{stream_id}:{video_file.stem}",
                    Path.root_path(),
                    data,
                )
                # Sometimes FFmpeg creates two video fragments at the same time, possibly due to a cache that FFmpeg
                # directly can download from YouTube. This is not wanted because the video_data_extractor could try to
                # open the same video twice While it's already removed.
                r.lrem(
                    "queue:video_data_extractor",
                    0,
                    f"{stream_id}/{video_file.name}",
                )
                r.lpush(
                    "queue:video_data_extractor",
                    f"{stream_id}/{video_file.name}",
                )
        r.json().set(
            "segment_list_information",
            f".{stream_id}",
            start + lines_read,
        )
