import os
from pathlib import Path


def generate_subtitle_file(video_path: os.PathLike | str, text: str, duration: int):
    """
    Generate a subtitle file for the given text and duration.

    :param video_path: path to save the generated subtitle to.
    :param text: text to use for the subtitle.
    :param duration: duration of the subtitle.

    :return: generated subtitle file.
    """

    video_path = Path(video_path)
    directory = video_path.parents[0]
    video_name = video_path.stem

    # Generate subtitle file.
    subtitle_path = directory / f"{video_name}.srt"
    with open(subtitle_path, "w") as file:
        file.write(f"1\n00:00:00,000 --> {duration}\n{text}\n")
