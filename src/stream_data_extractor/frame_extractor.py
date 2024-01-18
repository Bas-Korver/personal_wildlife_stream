import cv2


def get_frames_from_video(video_path, store_path, fps: int = 1, frames_to_get: int = 0):
    """
    Get frames from video with specified fps.

    :param video_path: path to video.
    :param fps: frames per second.
    :param frames_to_get: number of frames to get, when 0 it extracts frames from the full video.
    :return: list of frames.
    """

    retrieved_frames = 0

    video = cv2.VideoCapture(video_path)
    video_fps = int(video.get(cv2.CAP_PROP_FPS))
    video_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_interval = video_fps // fps

    frames_to_get = frames_to_get if frames_to_get > 0 else fps_interval

    for frame_i in range(0, video_frames, fps_interval):
        if retrieved_frames >= frames_to_get:
            break
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_i)
        ret, frame = video.read()

        if ret:
            cv2.imwrite(f"{store_path}/{frame_i}.png", frame)
            retrieved_frames += 1

    video.release()


if __name__ == "__main__":
    get_frames_from_video(
        "../stream_downloader/streams/Ihr_nwydXi0/20240112_113638.mp4",
        "./test",
        frames_to_get=8,
    )
