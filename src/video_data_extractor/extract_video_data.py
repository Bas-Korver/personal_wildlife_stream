import pathlib
import platform
import signal
import threading
import picologging
from redis.commands.json.path import Path

from db.redis_connection import RedisConnection
from modules.audio_extractor import extract_audio
from modules.frame_extractor import get_frames_from_video
from core.config import settings

r = RedisConnection().get_redis_client()
picologging.basicConfig(level=settings.PROGRAM_LOG_LEVEL)
event = threading.Event()


class DataExtractor(threading.Thread):
    def __init__(self, event):
        super().__init__()
        self.event = event

    def run(self):
        while True:
            if self.event.is_set():
                return

            # Get queue element
            try:
                video_path = pathlib.Path(r.brpop("queue:video_data_extractor", 10)[1])
            except TypeError:
                # TODO: this logging statement blocks the thread.
                # picologging.debug(f"Queue is empty, retrying")
                continue

            # Get directory and filename.
            filename = video_path.stem
            youtube_id = video_path.parent.name

            picologging.debug(
                f"Video_data_extractor: Got video {youtube_id}_{filename} from queue"
            )

            # Extract frames from video
            successful = get_frames_from_video(
                event, video_path, settings.FRAMES_PER_SECOND, settings.FRAMES_TO_GET
            )

            if not successful:
                picologging.error(f"Failed to extract frames from {video_path}")
                continue
            # Extract audio from video
            extract_audio(video_path)

            data = {
                "video_path": str(video_path),
                "motion": None,
                "image_detection": None,
                "audio_detection": None,
                "score": None,
            }

            # Save results.
            r.json().set(
                f"video_information:{youtube_id}:{video_path.stem}",
                Path.root_path(),
                data,
            )

            r.lpush("queue:level_1_detection", str(video_path))

            # TODO: make it configurable that audio detection will only be executed when motion is detected.
            r.lpush("queue:audio_detection", str(video_path))


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
        threads.append(DataExtractor(event))

    for thread in threads:
        thread.start()

    picologging.info("Started all threads for video extraction.")

    for thread in threads:
        while thread.is_alive():
            thread.join(1)
