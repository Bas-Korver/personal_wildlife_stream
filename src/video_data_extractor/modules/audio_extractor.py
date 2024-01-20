import os
import pathlib
import subprocess
import argparse
import threading

from core.config import settings


def extract_audio(video_path: str | os.PathLike):
    video_path = pathlib.Path(video_path)

    store_path = video_path.parents[0]
    filename = video_path.stem
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-i",
            video_path,
            "-q:a",
            "0",
            "-map",
            "a",
            "-loglevel",
            str(settings.FFMPEG_LOG_LEVEL),
            "-xerror",
            f"{store_path}/{filename}.mp3",
        ],
    )


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(prog="audio_extractor")
    #
    # parser.add_argument("-i", "--input", required=True)
    # parser.add_argument("-o", "--output", required=True)
    #
    # arguments = parser.parse_args()
    #
    # extract_audio(arguments.input, arguments.output)

    extract_audio(
        "../../streams/Ihr_nwydXi0/20240119_015408.mp4",
    )
