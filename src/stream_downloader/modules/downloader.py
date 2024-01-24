import os
import subprocess
import threading

import picologging
import yt_dlp
from redis.commands.json.path import Path
from yt_dlp.utils import DownloadError

from core.config import settings
from db.redis_connection import RedisConnection

# Global variables
r = RedisConnection().get_redis_client()
logger = picologging.getLogger("download_stream.downloader")

YDL = yt_dlp.YoutubeDL(
    {
        "format": "best[ext=mp4]",
        "quiet": True,
    }
)


class DownloadThread(threading.Thread):
    def __init__(self, stream, event):
        super().__init__()
        self.stream = stream
        self.event = event

    def run(self):
        video_information = None
        while video_information is None:
            if self.event.is_set():
                return

            # Try to get YouTube video information from youtube-dl
            try:
                logger.debug(f"Extracting video information from {self.stream}.")
                video_information = YDL.extract_info(self.stream, download=False)
            except DownloadError:
                logger.error(
                    f"Error while extracting video information retrying in 60 seconds."
                )
                self.event.wait(60)

        # Get stream id and stream url to use with FFmpeg and Redis.
        stream_id = video_information["id"]
        stream_url = video_information["url"]

        # When event is set, because the program is shutting down, return.
        if self.event.is_set():
            return

        logger.debug(f"Creating Redis entry for stream {stream_id}.")
        if not r.exists("stream_information"):
            r.json().set("stream_information", Path.root_path(), {})

        r.json().set("stream_information", f".{stream_id}", 0)

        os.makedirs(os.path.join(settings.SAVE_PATH, stream_id), exist_ok=True)
        exit_code = 1

        # Download stream with FFmpeg as long as there is no normal exit (exit code 0)
        while exit_code != 0:
            if self.event.is_set():
                return

            logger.info(f"Downloading stream {stream_id}.")
            # Download stream with FFmpeg
            output = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    str(settings.FFMPEG_LOG_LEVEL),
                    "-xerror",
                    "-i",
                    stream_url,
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
                    f"{settings.SAVE_PATH}/{stream_id}/%Y%m%d_%H%M%S.mp4",
                ]
            )
            exit_code = output.returncode

            # If exit code is not 0 and the event is not set, wait 60 seconds and retry
            if exit_code != 0 and not self.event.is_set():
                logger.error(f"Error while downloading stream retrying in 60 seconds.")
                self.event.wait(60)
