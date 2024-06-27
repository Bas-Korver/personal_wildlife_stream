import pathlib
import platform
import signal
import threading
import time

import requests

from core import settings
from db import RedisConnection
from modules import detect_birds, make_logger

# Global variables
r = RedisConnection().get_redis_client()
event = threading.Event()
logger = make_logger()


class ServiceExit(Exception):
    pass


class AudioDetection(threading.Thread):
    def __init__(self, event):
        super().__init__()
        self.event = event

    def run(self):
        while True:
            if self.event.is_set():
                return

            # Get queue element
            try:
                video_file = pathlib.Path(r.brpop("queue:audio_detection", 0.1)[1])
            except TypeError:
                logger.debug(f"Queue is empty, retrying in {settings.RETRY_TIME}")
                event.wait(settings.RETRY_TIME_SECONDS)
                continue

            # Save start time.
            start_time = time.time()

            # Get directory and video_name.
            video_path = settings.SAVE_PATH / video_file
            directory = video_path.parents[0]
            video_name = video_path.stem
            stream_id = video_path.parents[0].name

            # Load video data from redis.
            data = r.json().get(f"video_information:{stream_id}:{video_name}")

            new_data = {}
            # Check whether to get data after data extraction or after motion detection.
            if bool(data["motion"]) or not settings.DETECT_AUDIO_ONLY_AFTER_MOTION:
                # TODO make endpoint configurable
                # Get latitude and longitude of the stream.
                stream_information = requests.get(
                    f"{settings.FULL_PRIVATE_API_URL}/v1/internal-streams/streams/{stream_id}"
                ).json()

                # Detect audio.
                audio_path = directory / f"{video_name}.mp3"
                detections = detect_birds(
                    audio_path,
                    latitude=stream_information["latitude"],
                    longitude=stream_information["longitude"],
                )

                for detection in detections:
                    new_data[detection["common_name"]] = {
                        "scientific_name": detection["scientific_name"],
                        "confidence": round(detection["confidence"], 4),
                    }

                requests.post(
                    f"{settings.FULL_PRIVATE_API_URL}/v1/internal-streams/streams/{stream_id}/animals",
                    json=[{"animal": animal, "count": 1} for animal in new_data.keys()],
                )

            # Save results.
            r.json().set(
                f"video_information:{stream_id}:{video_name}",
                ".audio_detection",
                new_data,
            )

            # Save processing time.
            r.json().set(
                f"video_information:{stream_id}:{video_path.stem}",
                ".processing_times.audio_detection",
                time.time() - start_time,
            )

            # Push to next phase of pipeline.
            r.lrem("queue:video_ranking", 0, str(video_file.as_posix()))
            r.lpush("queue:video_ranking", str(video_file.as_posix()))


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
        threads.append(AudioDetection(event))

    try:
        for thread in threads:
            thread.start()
            logger.info("Started all threads for audio detection.")

        while True:
            time.sleep(0.5)
    except ServiceExit:
        event.set()
        for thread in threads:
            thread.join()
        logger.info("Stopped all threads for audio detection.")
