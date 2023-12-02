import cv2


def get_frames_from_video(video_path, fps=1) -> list:
    """
    Get frames from video with specified fps.

    :param video_path: path to video.
    :param fps: frames per second.
    :return: list of frames.
    """

    frames = []

    video = cv2.VideoCapture(video_path)
    video_fps = int(video.get(cv2.CAP_PROP_FPS))
    video_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_interval = video_fps // fps

    for frame_i in range(0, video_frames, fps_interval):
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_i)
        ret, frame = video.read()

        if ret:
            frames.append(frame)

    video.release()

    return frames
