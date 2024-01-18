import os
import pathlib
import subprocess
import threading

from yt_dlp.utils import DownloadError
import picologging

import yt_dlp

picologging.basicConfig(level=picologging.DEBUG)

YDL = yt_dlp.YoutubeDL(
    {
        "format": "best[ext=mp4]",
        "quiet": True,
    }
)

# TODO: Make this an api call.
YOUTUBE_URLS = [
    "https://www.youtube.com/watch?v=Ihr_nwydXi0",
    "https://www.youtube.com/watch?v=yPSYdCWRWFA",
]

STREAM_DOWNLOAD_TIME = 10
STREAM_DOWNLOAD_LOCATION = "./streams"


def download_streams():
    """
    Download all available streams.
    """
    threads = []
    for youtube_url in YOUTUBE_URLS:
        thread = threading.Thread(
            target=download_stream,
            args=(
                youtube_url,
                STREAM_DOWNLOAD_LOCATION,
                STREAM_DOWNLOAD_TIME,
            ),
        )

        threads.append(thread)

    for thread in threads:
        thread.start()

    picologging.info("Started all threads for stream download.")


def download_stream(stream: str, save_path: str = "./streams", time: int = 10):
    """
    Download specified stream with specified time interval to save path.

    :param stream: url of stream to download.
    :param save_path: path where to save the downloaded stream.
    :param time: time in seconds for intervals of stream save.
    """
    try:
        video_information = YDL.extract_info(stream, download=False)
    except DownloadError:
        picologging.warning(f"Error while extracting video information")
        return

    video_id = video_information["id"]
    video_url = video_information["url"]

    os.makedirs(os.path.join(save_path, video_id), exist_ok=True)

    subprocess.run(
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
            str(time),
            "-f",
            "segment",
            "-strftime",
            "1",
            "-hide_banner",
            "-loglevel",
            "warning",
            f"{save_path}/{video_id}/%Y%m%d_%H%M%S.mp4",
        ]
    )


if __name__ == "__main__":
    download_streams()
