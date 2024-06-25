import pathlib
import platform
import signal
import threading
import time

import cv2

from core import settings
from db import RedisConnection
from modules import motion_detection, make_logger

# Global variables
r = RedisConnection().get_redis_client()
event = threading.Event()
logger = make_logger()


class ServiceExit(Exception):
    pass


class MotionDetection(threading.Thread):
    def __init__(self, event):
        super().__init__()
        self.event = event

    def run(self):
        while True:
            if self.event.is_set():
                return

            # Get queue element
            try:
                video_file = pathlib.Path(
                    r.brpop("queue:level_1_detection_motion", 0.1)[1]
                )
            except TypeError:
                logger.debug(f"Queue is empty, retrying in {settings.RETRY_TIME}")
                event.wait(settings.RETRY_TIME_SECONDS)
                continue

            # Save start time.
            start_time = time.time()

            # Get directory and video name.
            video_path = settings.SAVE_PATH / video_file
            directory = video_path.parents[0]
            video_name = video_path.stem
            stream_id = video_path.parents[0].name

            logger.debug(
                f"Got video from queue",
                stream_id=stream_id,
                video_name=video_name,
            )

            # Get the saved frames for this video.
            frame_pngs = sorted(
                directory.glob(f"{video_name}_*.png"),
                key=lambda x: int(x.stem.rsplit("_", 1)[-1]),
            )
            frames = [cv2.imread(str(frame_png)) for frame_png in frame_pngs]

            if len(frames) < 2:
                logger.warning(
                    f"Video has less than 2 frames, skipping", video_name=video_name
                )
                continue

            # Run motion detection on the sorted frames.
            motion, _ = motion_detection(
                frames,
                settings.PIXEL_THRESHOLD_FOR_MOVEMENT,
                settings.MIN_PIXEL_CHANGE_COUNT_FOR_MOVEMENT,
            )

            # Save results.
            r.json().set(
                f"video_information:{stream_id}:{video_name}", ".motion", int(motion)
            )

            # Save processing time.
            r.json().set(
                f"video_information:{stream_id}:{video_path.stem}",
                ".processing_times.motion_detection",
                time.time() - start_time,
            )

            # Push to next level.
            r.lpush("queue:level_2_detection_image", str(video_file))


def handler(signum, frame):
    logger.info("Received a stop signal, shutting down")
    logger.debug("Interrupted by:", signum=signum, signame=signal.Signals(signum).name)
    raise ServiceExit


if __name__ == "__main__":
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    threads = []
    for _ in range(settings.THREAD_COUNT):
        threads.append(MotionDetection(event))

    try:
        for thread in threads:
            thread.start()
            logger.info("Started all threads for motion detection.")

        while True:
            time.sleep(0.5)
    except ServiceExit:
        event.set()
        for thread in threads:
            thread.join()
        logger.info("Stopped all threads for motion detection.")
