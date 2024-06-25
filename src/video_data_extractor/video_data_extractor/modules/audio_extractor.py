import os
import pathlib
import subprocess

from core import settings


def extract_audio(video_path: os.PathLike | str):
    """
    Extracts audio from video.
    :param video_path: Path to video.
    """
    from modules import make_logger

    logger = make_logger()

    video_path = pathlib.Path(video_path)

    directory = video_path.parents[0]
    video_name = video_path.stem
    logger.debug(f"Extracting audio", video_path=video_path)

    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            str(settings.FFMPEG_LOG_LEVEL),
            "-nostdin",
            "-i",
            str(video_path),
            "-q:a",
            "0",
            "-map",
            "a",
            f"{directory}\{video_name}.mp3",
        ],
    )
