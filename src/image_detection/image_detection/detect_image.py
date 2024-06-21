import pathlib
import platform
import signal
import threading
import time
from pathlib import Path

import cv2
import requests
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

MODELS = {}
DEFAULT_MODEL = torch.hub.load(
    "ultralytics/yolov5",
    "custom",
    f"{Path(__file__).resolve().parent}/../models/{settings.DEFAULT_MODEL_PATH}",
    force_reload=True,
)
DEFAULT_MODEL.to(DEVICE)


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
            stream_id = video_path.parent.name

            # Check desired model for this stream.
            stream_tag = requests.get(
                f"http://localhost:8003/v1/internal-streams/streams/{stream_id}"  # TODO: Make URL dynamic.
            ).json()["tag"]
            model = MODELS.get(stream_tag["id"])

            # If model is not loaded in yet, load model in for this stream.
            if model is None:
                # If the stream tag has a specific model, load in this model.
                if stream_tag["model"] is not None:
                    model = torch.hub.load(
                        "ultralytics/yolov5",
                        "custom",
                        f"{Path(__file__).resolve().parent}/../models/{stream_tag["model"]}",
                        force_reload=True,
                    )
                    MODELS[stream_tag["id"]] = model

                # If the stream tag has not specified a model, load in default model.
                else:
                    model = DEFAULT_MODEL
                    MODELS[stream_tag["id"]] = model

            # Load video data from redis.
            data = r.json().get(f"video_information:{stream_id}:{filename}")

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
                    model,
                    frames,
                    settings.MODEL_CONFIDENCE,
                )
                
            # Save detected animals to API.
            requests.post(
                f"http://localhost:8003/v1/internal-streams/streams/{stream_id}/animals", # TODO: Make URL dynamic.
                json=[{"animal": animal, "count": image_detections[animal]["count"]} for animal in image_detections.keys()]
            )

            # Save results.
            r.json().set(
                f"video_information:{stream_id}:{filename}",
                ".image_detection",
                image_detections,
            )

            # Save processing time.
            r.json().set(
                f"video_information:{stream_id}:{video_path.stem}",
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
