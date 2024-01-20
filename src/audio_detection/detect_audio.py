import pathlib
import platform
import signal
import threading

import picologging
from redis.commands.json.path import Path

from core.config import settings
from db.redis_connection import RedisConnection
from modules.detect_birds import detect_birds

r = RedisConnection().get_redis_client()
picologging.basicConfig(level=settings.PROGRAM_LOG_LEVEL)
event = threading.Event()


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
                video_path = pathlib.Path(r.brpop("queue:audio_detection", 10)[1])
            except TypeError:
                # TODO: this logging statement blocks the thread.
                # picologging.debug(f"Queue is empty, retrying")
                continue

            # Get directory and filename.
            directory = video_path.parents[0]
            filename = video_path.stem
            youtube_id = video_path.parent.name

            data = r.json().get(f"video_information:{youtube_id}:{filename}")

            audio_path = directory / f"{filename}.mp3"
            detections = detect_birds(audio_path)

            new_data = {}

            for detection in detections:
                new_data[detection["common_name"]] = {
                    "scientific_name": detection["scientific_name"],
                    "confidence": round(detection["confidence"], 4),
                }

            data["audio_detection"] = new_data

            # Save results.
            r.json().set(
                f"video_information:{youtube_id}:{filename}",
                Path.root_path(),
                data,
            )

            # Push to next phase of pipeline.
            r.lrem("queue:video_ranking", 0, str(video_path))
            r.lpush("queue:video_ranking", str(video_path))

            # TODO: Remove audio from disk.


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
        threads.append(AudioDetection(event))

    for thread in threads:
        thread.start()

    picologging.info("Started all threads for audio detection.")

    for thread in threads:
        while thread.is_alive():
            thread.join(1)
