import os
import subprocess
import threading

import yt_dlp
from yt_dlp.utils import DownloadError

from core import settings
from db import RedisConnection
from modules import make_logger

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
    """
    DownloadThread class to download.

    :param stream_id: The stream uuid from the database.
    :param stream_url: The stream url from the database,
     this equals to a url in the format of https://youtu.be/xxxxxxxxxxx.
    :param event: The event to signal the thread to stop.
    """

    def __init__(self, stream_id: str, stream_url: str, event):
        super().__init__()

        self.stream_id = stream_id
        self.stream_url = stream_url
        self.event = event

    def run(self):
        # Do some calculations
        stream_information = None

        while stream_information is None:
            # When event is set, because the program is shutting down, return.
            if self.event.is_set():
                return

            # Try to get YouTube stream information from youtube-dl and retry every retry_time_seconds as long as the
            # program runs.
            logger.debug(
                f"Extracting stream information.",
                stream_id=self.stream_id,
                stream_url=self.stream_url,
            )
            try:
                stream_information = YDL.extract_info(self.stream_url, download=False)
            except DownloadError:
                logger.warning(
                    f"Problem while extracting stream information retrying in {settings.RETRY_TIME}.",
                    stream_url=self.stream_url,
                )
                self.event.wait(settings.RETRY_TIME_SECONDS)

        # If stream is not live, do not download it, otherwise that stream will be downloaded a lot faster with FFMpeg
        # than the other live streams, which could cause problems down the line.
        # TODO make this configurable and/or handle prerecorded livestreams.
        if stream_information["is_live"] is False:
            logger.warning(
                f"Stream is not live, not downloading this stream.",
                stream_id=self.stream_id,
                stream_url=self.stream_url,
            )
            return

        # Get stream id and stream url to use with FFmpeg and Redis.
        youtube_stream_url = stream_information["url"]

        # When event is set, because the program is shutting down, return.
        if self.event.is_set():
            return

        logger.debug(
            f"Creating Redis entries.",
            stream_id=self.stream_id,
            stream_url=self.stream_url,
        )
        r.json().set("stream_information", f".{self.stream_id}", 0)
        r.json().set("segment_list_information", f".{self.stream_id}", 0)

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
                stream_url=self.stream_url,
                youtube_stream_url=youtube_stream_url,
            )

            # W
            # Download stream with FFmpeg
            process = subprocess.run(
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
                    str(settings.VIDEO_SEGMENT_TIME_SECONDS),
                    "-f",
                    "segment",
                    "-strftime",
                    "1",
                    "-segment_list",
                    f"{settings.SAVE_PATH}/{self.stream_id}/segment_list.txt",
                    "-segment_list_flags",
                    "live",
                    f"{settings.SAVE_PATH}/{self.stream_id}/%Y%m%d_%H%M%S.mp4",
                ]
            )
            exit_code = process.returncode

            # If exit code is not 0 and the event is not set, wait 60 seconds and retry
            if exit_code != 0 and not self.event.is_set():
                logger.warning(
                    f"Problem while downloading stream retrying in {settings.RETRY_TIME}"
                )
                self.event.wait(settings.RETRY_TIME_SECONDS)
