import os
import subprocess
import threading
from uuid import UUID

import yt_dlp
from redis.commands.json.path import Path
from yt_dlp.utils import DownloadError

from core import settings
from db import RedisConnection
from modules import make_logger
import requests

# Global variables
r = RedisConnection().get_redis_client()
logger = make_logger()
YDL = yt_dlp.YoutubeDL(
    {
        "format": "best[ext=mp4]",
        "quiet": settings.YT_DLP_QUIET,
    }
)


class DownloadThread(threading.Thread):
    def __init__(self, stream_id: str, stream_url: str, event):
        super().__init__()
        self.stream_id = stream_id
        self.stream_url = stream_url
        self.event = event

    def run(self):
        stream_information = None
        while stream_information is None:
            if self.event.is_set():
                return

            # Try to get YouTube stream information from youtube-dl
            try:
                logger.debug(
                    f"Extracting stream information.",
                    stream_id=self.stream_id,
                    youtube_url=self.stream_url,
                )
                stream_information = YDL.extract_info(self.stream_url, download=False)
            except DownloadError:
                logger.warning(
                    f"Problem while extracting stream information retrying in 60 seconds."
                )
                self.event.wait(60)

        # Get stream id and stream url to use with FFmpeg and Redis.
        youtube_stream_id = stream_information["id"]
        youtube_stream_url = stream_information["url"]

        # When event is set, because the program is shutting down, return.
        if self.event.is_set():
            return

        logger.debug(
            f"Creating Redis entry.",
            stream_id=self.stream_id,
            youtube_url=self.stream_url,
        )
        if not r.exists("stream_information"):
            r.json().set("stream_information", Path.root_path(), {})

        r.json().set("stream_information", f".{self.stream_id}", 0)

        os.makedirs(
            os.path.join(settings.SAVE_PATH, str(self.stream_id)), exist_ok=True
        )
        exit_code = 1

        # Download stream with FFmpeg as long as there is no normal exit (exit code 0)
        while exit_code != 0:
            if self.event.is_set():
                return

            logger.info(
                f"Downloading stream.",
                stream_id=self.stream_id,
                youtube_url=self.stream_url,
            )
            # Download stream with FFmpeg
            output = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    str(settings.FFMPEG_LOG_LEVEL),
                    "-xerror",
                    "-i",
                    youtube_stream_url,
                    "-c",
                    "copy",
                    "-reset_timestamps",
                    "1",
                    "-map",
                    "0",
                    "-segment_time",
                    str(settings.VIDEO_SEGMENT_TIME),
                    "-f",
                    "segment",
                    "-strftime",
                    "1",
                    f"{settings.SAVE_PATH}/{self.stream_id}/%Y%m%d_%H%M%S.mp4",
                ]
            )
            exit_code = output.returncode

            # If exit code is not 0 and the event is not set, wait 60 seconds and retry
            if exit_code != 0 and not self.event.is_set():
                logger.warning(
                    f"Problem while downloading stream retrying in 60 seconds."
                )
                self.event.wait(60)
