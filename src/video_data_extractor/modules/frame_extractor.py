import os
import pathlib

import cv2


def get_frames_from_video(
    event, video_path: str | os.PathLike, fps: int = 1, frames_to_get: int = 0
):
    """
    Get frames from video with specified fps.

    :param event: threading.Event() object.
    :param video_path: path to video.
    :param fps: frames per second.
    :param frames_to_get: number of frames to get, when 0 it extracts frames from the full video.
    :return: list of frames.
    """

    video_path = pathlib.Path(video_path)

    retrieved_frames = 0

    retries = 0
    while retries < 3:
        video = cv2.VideoCapture(str(video_path))
        video_fps = int(video.get(cv2.CAP_PROP_FPS))
        if video_fps > 0:
            retries = 3
        retries += 1
        if retries == 3:
            return False
        event.wait(3)

    video_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_interval = video_fps // fps

    frames_to_get = frames_to_get if frames_to_get > 0 else video_frames // fps_interval

    for frame_i in range(0, video_frames, fps_interval):
        if retrieved_frames >= frames_to_get or event.is_set():
            break
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_i)
        ret, frame = video.read()

        store_path = video_path.parents[0]
        filename = video_path.stem

        if ret:
            cv2.imwrite(f"{store_path}/{filename}_{frame_i}.png", frame)
            retrieved_frames += 1

    video.release()

    return True
