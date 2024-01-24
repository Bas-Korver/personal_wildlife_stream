import pathlib
import time
import subprocess

import picologging

from core.config import settings
from db.redis_connection import RedisConnection

# Global variables.
VIDEO_ITERATION_DELAY = 8.5  # TODO: Test with delay make configurable.
r = RedisConnection().get_redis_client()
picologging.basicConfig(
    level=settings.PROGRAM_LOG_LEVEL,
    format="%(levelname)s - %(name)s - Line: %(lineno)d - Thread: %(thread)d - %(message)s",
)
p_stream_selector = r.pubsub(ignore_subscribe_messages=True)
p_stream_selector.subscribe("stream_selector")
p_streamer = r.pubsub(ignore_subscribe_messages=True)
p_streamer.subscribe("streamer")


def start_stream_file(event):
    # Get the highest ranking video at start of the stream.
    video_key = r.rpop("stream_order")
    r.publish("stream_selector", video_key)

    # Create output file.
    output_file_path = "../streams/stream.ts"
    video_source_path = r.json().get(video_key, ".video_path")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            str(settings.FFMPEG_LOG_LEVEL),
            "-i",
            video_source_path,
            "-c",
            "copy",
            output_file_path,
        ]
    )

    while True:
        if event.is_set():
            picologging.debug("Stopping video stream as event is set.")
            return
        # Note start time of iteration.
        start_time = time.time()

        # Get highest ranking video.
        try:
            video_key = r.brpop("stream_order", 10)[1]
        except TypeError:
            picologging.debug(
                "Stopping video stream as no additional videos available."
            )
            break

        picologging.debug(f"Got video key: {video_key}")
        video_source_path = r.json().get(video_key, ".video_path")

        # Send message of chosen video.
        r.publish("stream_selector", video_key)

        # Create intermediate file for extension to stream.
        intermediate_file_path = f"intermediate_{time.strftime('%Y%m%d_%H%M%S')}.ts"
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                str(settings.FFMPEG_LOG_LEVEL),
                "-i",
                video_source_path,
                "-c",
                "copy",
                intermediate_file_path,
            ]
        )

        # Create intermediate file for stream up to this point.
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                str(settings.FFMPEG_LOG_LEVEL),
                "-i",
                output_file_path,
                "-c",
                "copy",
                "intermediate_stream.ts",
            ]
        )

        # Create new file with the extension added to the end of the stream video.
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                str(settings.FFMPEG_LOG_LEVEL),
                "-y",
                "-i",
                f"concat:{intermediate_file_path}|intermediate_stream.ts",
                "-c",
                "copy",
                f"{output_file_path}",
            ]
        )

        picologging.debug(f"Time needed to add new file: { time.time() - start_time }")

        # Remove intermediate files.
        pathlib.Path(intermediate_file_path).unlink()
        pathlib.Path()

        # Sleep for remaining time.
        sleep_time = max((0, VIDEO_ITERATION_DELAY - (time.time() - start_time)))
        picologging.debug(f"Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
