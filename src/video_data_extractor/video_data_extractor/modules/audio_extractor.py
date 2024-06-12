import os
import pathlib
import structlog
import subprocess

from core.config import settings

logger = structlog.get_logger()


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
