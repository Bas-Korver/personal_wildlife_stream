import pathlib
import platform
import signal
import threading
import time

from core import settings
from db import RedisConnection
from modules import extract_frames, extract_audio, make_logger

# Global variables
r = RedisConnection().get_redis_client()
event = threading.Event()
logger = make_logger()


class ServiceExit(Exception):
    pass


class DataExtractor(threading.Thread):
    def __init__(self, event):
        super().__init__()
        self.event = event

    def run(self):
        while True:
            # When event is set, because the program is shutting down, return.
            if self.event.is_set():
                return

            # Get queue element
            try:
                video_file = pathlib.Path(r.brpop("queue:video_data_extractor", 0.1)[1])
            except TypeError:
                logger.debug(f"Queue is empty, retrying in {settings.RETRY_TIME}")
                event.wait(settings.RETRY_TIME_SECONDS)
                continue

            # Save start time.
            start_time = time.time()

            # Get directory and video_name.
            video_path = settings.SAVE_PATH / video_file
            directory = video_path.parents[0]
            stream_id = video_path.parents[0].name
            video_name = video_path.stem

            logger.debug(
                f"Got video from queue",
                video_path=video_path,
                stream_id=stream_id,
                video_name=video_name,
            )

            # Extract frames from video
            successful = extract_frames(
                event, video_path, settings.FRAMES_PER_SECOND, settings.FRAMES_TO_GET
            )

            if not successful:
                logger.error(f"Failed to extract frames", video_path=video_path)
                # Get the saved frames for this video.
                frame_pngs = directory.glob(f"{video_name}_*.png")

                # Delete the pngs for this section.
                for frame_png in frame_pngs:
                    frame_png.unlink()
                continue

            # Extract audio from video
            extract_audio(video_path)

            # Save processing time.
            r.json().set(
                f"video_information:{stream_id}:{video_path.stem}",
                ".processing_times.data_extractor",
                time.time() - start_time,
            )

            # Add video to the queue for level 1 detection
            r.lpush("queue:level_1_detection_motion", str(video_file.as_posix()))
            r.lpush("queue:audio_detection", str(video_file.as_posix()))


def handler(signum, frame):
    logger.info("Received a stop signal, shutting down")
    logger.debug("Interrupted by:", signum=signum, signame=signal.Signals(signum).name)
    raise ServiceExit


if __name__ == "__main__":
    # Register signal handlers
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    # Start threads
    threads = []
    for _ in range(settings.THREAD_COUNT):
        threads.append(DataExtractor(event))

    try:
        for thread in threads:
            thread.start()
            logger.info("Started all threads for video extraction.")

        while True:
            time.sleep(0.5)
    except ServiceExit:
        event.set()
        for thread in threads:
            thread.join()
        logger.info("Stopped all threads for video extraction.")
