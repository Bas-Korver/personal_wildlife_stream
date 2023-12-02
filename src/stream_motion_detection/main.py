import os
import numpy as np
import cv2

from ..utils import get_frames_from_video

STREAM_DOWNLOAD_LOCATION = "../stream_downloader/streams"


def filter_streams_based_on_motion(threshold=30, min_pixel_count=100):
    """

    :param threshold:
    :param min_pixel_count:
    """

    stream_ids = [
        stream
        for stream in os.listdir(STREAM_DOWNLOAD_LOCATION)
        if os.path.isdir(os.path.join(STREAM_DOWNLOAD_LOCATION, stream))
    ]

    animal_detection_streams = []
    for stream_id in stream_ids:
        video = get_current_stream_file(stream_id)

        # TODO: Save processed stream section.

        video_frames = get_frames_from_video(
            os.path.join(STREAM_DOWNLOAD_LOCATION, stream_id, video), 1
        )

        height, width, _ = video_frames[0].shape
        out = cv2.VideoWriter(
            f"extracted_frames_{ stream_id }_{video}",
            cv2.VideoWriter_fourcc(*"mp4v"),
            1,
            video_frames[0].shape[:2][::-1],
        )

        for frame in video_frames:
            out.write(frame)
        out.release()

        movement, _ = motion_detection(video_frames, threshold, min_pixel_count)

        if movement:
            # TODO: Make available for animal detection.
            animal_detection_streams.append(
                os.path.join(STREAM_DOWNLOAD_LOCATION, stream_id, video)
            )

    print(animal_detection_streams)


def get_current_stream_file(stream_id):
    """
    Get file to check for motion, currently oldest found stream is selected.
    :param stream_id:
    """
    stream_location = os.path.join(STREAM_DOWNLOAD_LOCATION, stream_id)

    videos = [
        video
        for video in os.listdir(stream_location)
        if os.path.isfile(os.path.join(stream_location, video))
        and video.lower().endswith(".mp4")
    ]

    if not videos:
        return None

    oldest_video = videos[0]
    oldest_video_timestamp = os.path.getctime(
        os.path.join(stream_location, oldest_video)
    )

    for video in videos[1:]:
        video_timestamp = os.path.getctime(os.path.join(stream_location, video))

        if video_timestamp < oldest_video_timestamp:
            oldest_video = video
            oldest_video_timestamp = video_timestamp

    return oldest_video


def motion_detection(frames, threshold=30, min_pixel_count=1000):
    """
    Run motion detection on a set of frames.
    :param frames:
    :param threshold:
    :param min_pixel_count:
    :return:
    """

    # Check each frame from movement compared to the previous frame.
    difference_frames = []
    movement = False

    for i in range(1, len(frames)):
        gray_frame = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)

        previous_gray_frame = cv2.cvtColor(frames[i - 1], cv2.COLOR_BGR2GRAY)
        previous_gray_frame = cv2.GaussianBlur(previous_gray_frame, (5, 5), 0)

        difference_frame = cv2.absdiff(gray_frame, previous_gray_frame)

        _, difference_threshold = cv2.threshold(
            difference_frame, threshold, 255, cv2.THRESH_BINARY
        )

        movement_detected = cv2.countNonZero(difference_threshold) > min_pixel_count
        difference_frames.append([movement_detected, difference_threshold])

        movement |= movement_detected

    return movement, np.array(difference_frames, dtype="object")


if __name__ == "__main__":
    filter_streams_based_on_motion()
