import os
import subprocess
import threading

import picologging
import yt_dlp
from yt_dlp.utils import DownloadError

from core.config import settings

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

            try:
                video_information = YDL.extract_info(self.stream, download=False)
            except DownloadError:
                picologging.error(
                    f"Error while extracting video information retrying in 60 seconds."
                )
                self.event.wait(60)

        video_id = video_information["id"]
        video_url = video_information["url"]

        os.makedirs(os.path.join(settings.SAVE_PATH, video_id), exist_ok=True)
        exit_code = 1

        while exit_code != 0:
            if self.event.is_set():
                return

            output = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    video_url,
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
                    "-hide_banner",
                    "-loglevel",
                    str(settings.FFMPEG_LOG_LEVEL),
                    "-xerror",
                    f"{settings.SAVE_PATH}/{video_id}/%Y%m%d_%H%M%S.mp4",
                ]
            )
            exit_code = output.returncode
            if exit_code != 0:
                picologging.error(
                    f"Error while downloading stream retrying in 60 seconds."
                )
                self.event.wait(60)
