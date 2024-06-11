import pathlib
import platform
import signal
import threading
import time

import structlog

from core.config import settings
from db.redis_connection import RedisConnection
from modules.detect_birds import detect_birds

# Global variables
r = RedisConnection().get_redis_client()
structlog.stdlib.recreate_defaults(log_level=settings.PROGRAM_LOG_LEVEL)
logger = structlog.get_logger()
event = threading.Event()


class AudioDetection(threading.Thread):
    def __init__(self, event):
        super().__init__()
        self.event = event

    def run(self):
        while True:
            if self.event.is_set():
                return

            # Check whether to get data after data extraction or after motion detection.

            # Get queue element
            try:
                video_path = pathlib.Path(r.brpop("queue:audio_detection", 10)[1])
            except TypeError:
                logger.debug(f"Queue is empty, retrying")
                continue

            # Save start time.
            start_time = time.time()

            # Get directory and filename.
            directory = video_path.parents[0]
            filename = video_path.stem
            youtube_id = video_path.parent.name

            # Load video data from redis.
            data = r.json().get(f"video_information:{youtube_id}:{filename}")

            new_data = {}

            if bool(data["motion"]) or not settings.DETECT_AUDIO_ONLY_AFTER_MOTION:
                # Detect audio.
                audio_path = directory / f"{filename}.mp3"
                detections = detect_birds(audio_path)

                for detection in detections:
                    new_data[detection["common_name"]] = {
                        "scientific_name": detection["scientific_name"],
                        "confidence": round(detection["confidence"], 4),
                    }

            # Save results.
            r.json().set(
                f"video_information:{youtube_id}:{filename}",
                ".audio_detection",
                new_data,
            )

            # Save processing time.
            r.json().set(
                f"video_information:{youtube_id}:{video_path.stem}",
                ".processing_times.audio_detection",
                time.time() - start_time,
            )

            # Push to next phase of pipeline.
            r.lrem("queue:video_ranking", 0, str(video_path))
            r.lpush("queue:video_ranking", str(video_path))


def handler(signum, frame):
    logger.info(f"Interrupted by {signum}, shutting down")
    event.set()


if __name__ == "__main__":
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    threads = []
    for _ in range(settings.THREAD_COUNT):
        threads.append(AudioDetection(event))

    for thread in threads:
        thread.start()

    logger.info("Started all threads for audio detection.")

    for thread in threads:
        while thread.is_alive():
            thread.join(1)
