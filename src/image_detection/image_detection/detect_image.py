import pathlib
import platform
import signal
import threading
import time

import cv2
import structlog
import torch

from core.config import settings
from db.redis_connection import RedisConnection
from modules.image_detection import image_detection

# Global variables
r = RedisConnection().get_redis_client()
structlog.stdlib.recreate_defaults(log_level=settings.PROGRAM_LOG_LEVEL)
logger = structlog.get_logger()
event = threading.Event()

# Load model
DEVICE = torch.device(settings.DEVICE)
MODEL = torch.hub.load(
    "ultralytics/yolov5", "custom", str(settings.MODEL_PATH), force_reload=True
)
MODEL.to(DEVICE)


class ImageDetection:
    def __init__(self, event):
        self.event = event

    def run(self):
        while True:
            if self.event.is_set():
                return

            # Get queue element
            try:
                video_path = pathlib.Path(
                    r.brpop("queue:level_2_detection_image", 10)[1]
                )
            except TypeError:
                logger.debug(f"Queue is empty, retrying")
                continue

            # Save start time.
            start_time = time.time()

            # Get directory and filename for motion detection.
            directory = video_path.parents[0]
            filename = video_path.stem
            youtube_id = video_path.parent.name

            # Load video data from redis.
            data = r.json().get(f"video_information:{youtube_id}:{filename}")

            image_detections = {}
            frame_pngs = None
            if bool(data["motion"]):
                # Get the saved frames for this video.
                frame_pngs = sorted(
                    directory.glob(f"{filename}_*.png"),
                    key=lambda x: int(x.stem.rsplit("_", 1)[-1]),
                )
                frames = [cv2.imread(str(frame_png)) for frame_png in frame_pngs]

                # Run image detection on the specified frames.
                image_detections = image_detection(
                    MODEL,
                    frames,
                    settings.MODEL_CONFIDENCE,
                )

            # Save results.
            r.json().set(
                f"video_information:{youtube_id}:{filename}",
                ".image_detection",
                image_detections,
            )

            # Save processing time.
            r.json().set(
                f"video_information:{youtube_id}:{video_path.stem}",
                ".processing_times.image_detection",
                time.time() - start_time,
            )

            # Push to next phase of pipeline.
            r.lrem("queue:video_ranking", 0, str(video_path))
            r.lpush("queue:video_ranking", str(video_path))

            # If the pngs were not loaded in yet, load them in.
            if frame_pngs is None:
                frame_pngs = directory.glob(f"{filename}_*.png")

            # Delete the pngs for this section.
            for frame_png in frame_pngs:
                frame_png.unlink()


def handler(signum, frame):
    logger.info(f"Interrupted by {signum}, shutting down")
    event.set()


if __name__ == "__main__":
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    detection = ImageDetection(event)
    detection.run()

    logger.info("Started image detection.")
