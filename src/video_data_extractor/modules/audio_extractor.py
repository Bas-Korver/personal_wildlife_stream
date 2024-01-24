import os
import pathlib
import subprocess

import picologging

from core.config import settings

logger = picologging.getLogger("extract_video_data.audio_extractor")


def extract_audio(video_path: str | os.PathLike):
    """
    Extracts audio from video.
    :param video_path: Path to video.
    """

    video_path = pathlib.Path(video_path)

    store_path = video_path.parents[0]
    filename = video_path.stem
    logger.debug(f"Extracting audio from {video_path}")
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            str(settings.FFMPEG_LOG_LEVEL),
            "-nostdin",
            "-i",
            video_path,
            "-q:a",
            "0",
            "-map",
            "a",
            f"{store_path}/{filename}.mp3",
        ],
    )
