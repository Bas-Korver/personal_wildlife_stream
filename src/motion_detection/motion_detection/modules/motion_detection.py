import cv2
import numpy as np

from modules import make_logger

# Global variables
logger = make_logger()


def motion_detection(
    frames: list,
    threshold: int = 30,
    min_pixel_count: int = 1000,
) -> tuple[bool, np.ndarray]:
    """
    Run motion detection on a set of frames.
    :param frames: list of frames
    :param threshold: threshold for pixel difference
    :param min_pixel_count: minimum amount of pixels that need to be different to classify as movement
    :return: (bool, np.ndarray)
    """

    # Check each frame from movement compared to the previous frame.
    difference_frames = []
    movement = False

    logger.debug(f"Running motion detection on {len(frames)} frames")
    for i in range(1, len(frames)):
        # Convert frames to grayscale and apply a gaussian blur.
        gray_frame = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)

        previous_gray_frame = cv2.cvtColor(frames[i - 1], cv2.COLOR_BGR2GRAY)
        previous_gray_frame = cv2.GaussianBlur(previous_gray_frame, (5, 5), 0)

        # Get difference between the two frames.
        difference_frame = cv2.absdiff(gray_frame, previous_gray_frame)

        # Threshold this difference to determine movement on a pixel level.
        _, difference_threshold = cv2.threshold(
            difference_frame, threshold, 255, cv2.THRESH_BINARY
        )

        # Check if the detected amount of movement pixels exceeds the minimum amount required to classify as movement.
        movement_detected = cv2.countNonZero(difference_threshold) > min_pixel_count
        difference_frames.append([movement_detected, difference_threshold])

        movement |= movement_detected

    return movement, np.array(difference_frames, dtype="object")
