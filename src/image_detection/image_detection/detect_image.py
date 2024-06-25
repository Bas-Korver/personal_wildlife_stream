import pathlib
import platform
import signal
import threading
import time
from pathlib import Path

import cv2
import requests
import torch

from core import settings
from db import RedisConnection
from modules import image_detection, make_logger

# Global variables
r = RedisConnection().get_redis_client()
event = threading.Event()
logger = make_logger()

# Load model
DEVICE = torch.device(settings.DEVICE)

MODELS = {}
DEFAULT_MODEL = torch.hub.load(
    "ultralytics/yolov5",
    "custom",
    str(settings.DEFAULT_MODEL_PATH),
    force_reload=True,
)
DEFAULT_MODEL.to(DEVICE)


class ServiceExit(Exception):
    pass


class ImageDetection:
    def __init__(self, event):
        self.event = event

    def run(self):
        while True:
            if self.event.is_set():
                return

            # Get queue element
            try:
                video_file = pathlib.Path(
                    r.brpop("queue:level_2_detection_image", 0.1)[1]
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

            # Check desired model for this stream.
            stream_tag = requests.get(
                f"{settings.FULL_PRIVATE_API_URL}/v1/internal-streams/streams/{stream_id}"  # TODO: Make URL dynamic.
            ).json()["tag"]
            model = MODELS.get(stream_tag["id"])

            # If model is not loaded in yet, load model in for this stream.
            if model is None:
                # If the stream tag has a specific model, load in this model.
                if stream_tag["model"] is not None:
                    model = torch.hub.load(
                        "ultralytics/yolov5",
                        "custom",
                        str(
                            settings.DEFAULT_MODEL_PATH.parents[0] / stream_tag["model"]
                        ),
                        force_reload=True,
                    )
                    MODELS[stream_tag["id"]] = model

                # If the stream tag has not specified a model, load in default model.
                else:
                    model = DEFAULT_MODEL
                    MODELS[stream_tag["id"]] = model

            # Load video data from redis.
            data = r.json().get(f"video_information:{stream_id}:{video_name}")

            image_detections = {}
            frame_pngs = None
            if bool(data["motion"]):
                # Get the saved frames for this video.
                frame_pngs = sorted(
                    directory.glob(f"{video_name}_*.png"),
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
                    f"http://localhost:8003/v1/internal-streams/streams/{stream_id}/animals",  # TODO: Make URL dynamic.
                    json=[
                        {"animal": animal, "count": image_detections[animal]["count"]}
                        for animal in image_detections.keys()
                    ],
                )

            # Save results.
            r.json().set(
                f"video_information:{stream_id}:{video_name}",
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
            r.lrem("queue:video_ranking", 0, str(video_file))
            r.lpush("queue:video_ranking", str(video_file))

            # If the pngs were not loaded in yet, load them in.
            if frame_pngs is None:
                frame_pngs = directory.glob(f"{video_name}_*.png")

            # Delete the pngs for this section.
            for frame_png in frame_pngs:
                frame_png.unlink()


def handler(signum, frame):
    logger.info("Received a stop signal, shutting down")
    logger.debug("Interrupted by:", signum=signum, signame=signal.Signals(signum).name)
    raise ServiceExit


if __name__ == "__main__":
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    detection = ImageDetection(event)

    try:
        detection.run()
        logger.info("Started image detection")

        while True:
            time.sleep(0.5)
    except ServiceExit:
        event.set()
        logger.info("Stopped image detection.")
