import pathlib
import platform
import signal
import threading
import time

from core import settings
from db import RedisConnection
from modules import stream_score, make_logger

# Global variables
r = RedisConnection().get_redis_client()
event = threading.Event()
logger = make_logger()


class ServiceExit(Exception):
    pass


class StreamRanking(threading.Thread):
    def __init__(self, event):
        super().__init__()
        self.event = event

    def run(self):
        while True:
            if self.event.is_set():
                return

            # Get queue element
            try:
                # TODO use LPOS
                video_file = pathlib.Path(r.brpop("queue:video_ranking", 0.1)[1])
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

            # Load video data from redis.
            data = r.json().get(f"video_information:{stream_id}:{video_name}")

            # Check if stream has image and audio detection results.
            # if data["image_detection"] is None or data["audio_detection"] is None:
            if data["image_detection"] is None or data["narration_subtitle"] is None:
                r.lrem("queue:video_ranking", 0, str(video_file.as_posix()))
                r.rpush("queue:video_ranking", str(video_file.as_posix()))
                continue

            # Save stream ranking.
            score = stream_score(
                stream_id, data["image_detection"], data["audio_detection"]
            )

            # Save results.
            r.json().set(f"video_information:{stream_id}:{video_name}", ".score", score)

            # Save processing time.
            r.json().set(
                f"video_information:{stream_id}:{video_path.stem}",
                ".processing_times.motion_detection",
                time.time() - start_time,
            )

            logger.debug(
                f"Saved stream ranking",
                stream_id=stream_id,
                video_name=video_name,
                score=score,
            )

            # Get the saved frames for this video.
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

    thread = StreamRanking(event)
    thread.run()

    logger.info("Started stream ranking.")
