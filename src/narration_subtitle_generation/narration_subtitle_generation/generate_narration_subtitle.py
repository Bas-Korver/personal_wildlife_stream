import pathlib
import platform
import signal
import threading
import time

from PIL import Image
from numpy import asarray

from core import settings
from db import RedisConnection
from modules import (
    speech_generation,
    text_generation,
    generate_subtitle_file,
    mix_video,
    make_logger,
)

# Global variables
r = RedisConnection().get_redis_client()
event = threading.Event()
logger = make_logger()


class ServiceExit(Exception):
    pass


class SpeechSubtitleGeneration:
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
                video_file = pathlib.Path(
                    r.brpop("queue:narration_subtitle_generation", 0.1)[1]
                )
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

            # IDEA: when audio detection is also used for narration and subtitle generation, there needs to come a check
            # like rank_stream.py to check if the audio detection and image detection are finished.
            # If not, the video fragment is put back in the queue.

            logger.debug(
                f"Got video from queue",
                video_path=video_path,
                stream_id=stream_id,
                video_name=video_name,
            )

            data = r.json().get(f"video_information:{stream_id}:{video_name}")
            done_some_narrating = False
            if data["image_detection"]:
                frame_pngs = sorted(
                    directory.glob(f"{video_name}_*.png"),
                    key=lambda x: int(x.stem.rsplit("_", 1)[-1]),
                )

                # IDEA: select different frames to instead of always the first one
                # Generate text (subtitles) for the video fragment.
                logger.info(f"Generating text", video_path=video_path)
                text = text_generation(
                    asarray(Image.open(frame_pngs[0])), data["image_detection"]
                )
                logger.info(f"Generating subtitle file", video_path=video_path)
                generate_subtitle_file(video_path, text, data["video_duration"])
                logger.info(f"Generating speech", video_path=video_path)
                speech_generation(video_path, text)
                logger.info(f"Mixing video", video_path=video_path)
                mix_video(video_path, data["video_duration"])
                done_some_narrating = True

            r.json().set(
                f"video_information:{stream_id}:{video_path.stem}",
                ".processing_times.narration_subtitle_generation",
                time.time() - start_time,
            )

            # Save processing time.
            r.json().set(
                f"video_information:{stream_id}:{video_path.stem}",
                ".narration_subtitle",
                int(done_some_narrating),
            )

            # Push to next phase of pipeline.
            r.lrem("queue:video_ranking", 0, str(video_file.as_posix()))
            r.lpush("queue:video_ranking", str(video_file.as_posix()))


def handler(signum, frame):
    logger.info("Received a stop signal, shutting down")
    logger.debug("Interrupted by:", signum=signum, signame=signal.Signals(signum).name)
    raise ServiceExit


if __name__ == "__main__":
    logger.debug("Starting narration_subtitle_generation")
    # Register signal handlers
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    narration_subs = SpeechSubtitleGeneration(event)

    try:
        narration_subs.run()
        logger.info("Started narration_subtitle_generation.")

        while True:
            time.sleep(0.5)
    except ServiceExit:
        event.set()
        logger.info("Stopped narration_subtitle_generation.")
