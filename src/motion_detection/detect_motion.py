import pathlib
import platform
import signal
import threading

import cv2
import picologging
from redis.commands.json.path import Path

from core.config import settings
from db.redis_connection import RedisConnection
from modules.motion_detection import motion_detection

r = RedisConnection().get_redis_client()
picologging.basicConfig(level=settings.PROGRAM_LOG_LEVEL)
event = threading.Event()


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
                video_path = pathlib.Path(r.brpop("queue:level_1_detection", 10)[1])
            except TypeError:
                # TODO: this logging statement blocks the thread.
                # picologging.debug(f"Queue is empty, retrying")
                continue

            # Get directory and filename for motion detection.
            directory = video_path.parents[0]
            filename = video_path.stem
            youtube_id = video_path.parent.name

            # Get the saved frames for this video.
            frame_pngs = sorted(
                directory.glob(f"{filename}_*.png"),
                key=lambda x: int(x.stem.rsplit("_", 1)[-1]),
            )
            frames = [cv2.imread(str(frame_png)) for frame_png in frame_pngs]

            if len(frames) < 2:
                picologging.warning(
                    f"Video {filename} has less than 2 frames, skipping"
                )
                continue

            # Run motion detection on the sorted frames.
            motion, _ = motion_detection(
                frames,
                settings.PIXEL_THRESHOLD_FOR_MOVEMENT,
                settings.MIN_PIXEL_CHANGE_COUNT_FOR_MOVEMENT,
            )

            # Load video data from redis.
            data = r.json().get(f"video_information:{youtube_id}:{filename}")

            data["motion"] = int(motion)

            # Save results.
            r.json().set(
                f"video_information:{youtube_id}:{filename}", Path.root_path(), data
            )

            # Push to next level.
            r.lpush("queue:level_2_detection", str(video_path))


def handler(signum, frame):
    picologging.info(f"Interrupted by {signum}, shutting down")
    event.set()


if __name__ == "__main__":
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    threads = []
    for _ in range(settings.THREAD_COUNT):
        threads.append(MotionDetection(event))

    for thread in threads:
        thread.start()

    picologging.info("Started all threads for motion detection.")

    for thread in threads:
        while thread.is_alive():
            thread.join(1)
