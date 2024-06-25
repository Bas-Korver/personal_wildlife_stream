import pathlib
import subprocess
import time

from core import settings
from db import RedisConnection
from modules import make_logger

# Global variables.
VIDEO_ITERATION_DELAY = 8.5  # TODO: Test with delay make configurable.
r = RedisConnection().get_redis_client()
logger = make_logger()
p_stream_selector = r.pubsub(ignore_subscribe_messages=True)
p_stream_selector.subscribe("stream_selector")
p_streamer = r.pubsub(ignore_subscribe_messages=True)
p_streamer.subscribe("streamer")


def start_stream_file(event):
    # Get the highest ranking video at start of the stream.
    video_key = r.rpop("stream_order")
    r.publish("stream_selector", video_key)

    # Create output file.
    # TODO: make this configurable
    output_file_path = settings.SAVE_PATH / "stream.ts"
    video_file = r.json().get(video_key, ".video_path")
    video_path = settings.SAVE_PATH / video_file
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            str(settings.FFMPEG_LOG_LEVEL),
            "-i",
            video_path,
            "-c",
            "copy",
            output_file_path,
        ]
    )

    while True:
        if event.is_set():
            logger.debug("Stopping video stream as event is set.")
            return
        # Note start time of iteration.
        start_time = time.time()

        # Get highest ranking video.
        max_retries = 3
        for i in range(max_retries):
            try:
                video_key = r.brpop("stream_order", 10)[1]
            except TypeError:
                if i >= max_retries - 1:
                    logger.debug(
                        "Stopping video stream as no additional videos available."
                    )
                    return
                event.wait(2)
            else:
                break

        logger.debug(f"Got video key: {video_key}")
        video_path = r.json().get(video_key, ".video_path")

        # Send message of chosen video.
        r.publish("stream_selector", video_key)

        # Create intermediate file for extension to stream.
        intermediate_file_path = f"intermediate_{time.strftime('%Y%m%d_%H%M%S')}.ts"
        logger.debug("Create intermediate file for extension to stream.")
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                str(settings.FFMPEG_LOG_LEVEL),
                "-i",
                video_path,
                "-c",
                "copy",
                "-bsf:v",
                "h264_mp4toannexb",
                intermediate_file_path,
            ]
        )

        # Create intermediate file for stream up to this point.
        logger.debug("Create intermediate file for stream up to this point.")
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
                "-bsf:v",
                "h264_mp4toannexb",
                "intermediate_stream.ts",
            ]
        )

        # Create new file with the extension added to the end of the stream video.
        logger.debug(
            "Create new file with the extension added to the end of the stream video."
        )
        with open("concat_list.txt", "w") as f:
            f.write(f"file '{intermediate_file_path}'\n")
            f.write(f"file 'intermediate_stream.ts'\n")

        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                str(settings.FFMPEG_LOG_LEVEL),
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                "concat_list.txt",
                "-c",
                "copy",
                output_file_path,
            ]
        )
        # subprocess.run(
        #     [
        #         "ffmpeg",
        #         "-loglevel",
        #         str(settings.FFMPEG_LOG_LEVEL),
        #         "-y",
        #         "-i",
        #         f"concat:{intermediate_file_path}|intermediate_stream.ts",
        #         "-c",
        #         "copy",
        #         f"{output_file_path}",
        #     ]
        # )

        logger.debug(f"Time needed to add new file: {time.time() - start_time}")

        # Remove intermediate files.
        pathlib.Path(intermediate_file_path).unlink()
        pathlib.Path()

        # Sleep for remaining time.
        sleep_time = max((0, VIDEO_ITERATION_DELAY - (time.time() - start_time)))
        logger.debug(f"Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
