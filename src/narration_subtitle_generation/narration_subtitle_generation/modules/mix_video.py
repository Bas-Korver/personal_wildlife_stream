import os
import subprocess
import sys
from pathlib import Path

from core import settings


def mix_video(video_path: os.PathLike | str, duration: str) -> None:
    """
    Mix the given video and audio into a single video.

    :param video_path: path to the video to mix.
    :param duration: duration of the video.
    """

    video_path = Path(video_path)
    directory = video_path.parents[0]
    video_name = video_path.stem
    audio_path = directory / f"{video_name}.wav"
    subtitle_path = directory / f"{video_name}.srt"
    output_path = directory / f"{video_name}_edited.mp4"
    subtitle_path_escaped = str(subtitle_path).replace("\\", "/").replace(":", "\\:")
    time_parts = duration.split(",")
    time_main = time_parts[0].split(":")

    milliseconds = int(time_parts[1])
    hours = int(time_main[0])
    minutes = int(time_main[1])
    seconds = int(time_main[2])
    duration_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            str(settings.FFMPEG_LOG_LEVEL),
            "-i",
            str(video_path),
            "-i",
            audio_path,
            "-filter_complex",
            # "[0:a][1:a]amerge=inputs=2[a]",
            "[0:a]apad[aud1];[1:a]apad[aud2];[aud1][aud2]amerge=inputs=2[a]",
            "-map",
            "0:v",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-ac",
            "2",
            "-t",
            str(duration_seconds),
            "-vf",
            f"subtitles='{subtitle_path_escaped}'",
            str(output_path),
        ]
    )

    # removed the original video, audio and subtitle files
    video_path.unlink()
    audio_path.unlink()
    subtitle_path.unlink()

    # rename the output file to the original video name
    output_path.rename(video_path)
