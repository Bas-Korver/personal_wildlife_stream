import subprocess

from db import RedisConnection
from core import settings
from modules import make_logger

r = RedisConnection().get_redis_client()
logger = make_logger()
p_stream_selector = r.pubsub(ignore_subscribe_messages=True)
p_stream_selector.subscribe("stream_selector")

p_streamer = r.pubsub(ignore_subscribe_messages=True)
p_streamer.subscribe("streamer")


def start_stream(stream_key, ffmpeg_log_level):
    logger.info("Start livestreaming")

    # Starting livestream.
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            str(ffmpeg_log_level),
            "-re",
            "-i",
            str(settings.SAVE_PATH / "stream.ts"),
            "-r",
            "30",
            "-g",
            "120",
            "-c:v",
            "libx264",
            "-preset",
            "superfast",
            "-b:v",
            "1500k",
            "-maxrate",
            "1500k",
            "-bufsize",
            "6000k",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-f",
            "flv",
            f"rtmp://a.rtmp.youtube.com/live2/{stream_key}",
        ]
    )
