import subprocess

import picologging

from db.redis_connection import RedisConnection

r = RedisConnection().get_redis_client()
p_stream_selector = r.pubsub(ignore_subscribe_messages=True)
p_stream_selector.subscribe("stream_selector")

p_streamer = r.pubsub(ignore_subscribe_messages=True)
p_streamer.subscribe("streamer")


def start_stream(stream_key, ffmpeg_log_level):
    # ffmpeg -re -i ../streams/stream.ts -r 30 -g 60 -c:v libx264 -preset fast -b:v 2500k -maxrate 2500k -bufsize 5000k -c:a aac -b:a 128k -f flv rtmp://a.rtmp.youtube.com/live2/fz7r-tbdx-swd0-m1vk-44j5
    # ffmpeg -re -i ./src/streams/stream.ts -r 30 -g 60 -c:v libx264 -preset fast -b:v 2500k -maxrate 2500k -bufsize 5000k -c:a aac -b:a 128k -f flv -flvflags no_duration_filesize rtmp://a.rtmp.youtube.com/live2/fz7r-tbdx-swd0-m1vk-44j5

    picologging.info("Start livestreaming")

    # Starting livestream.
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            str(ffmpeg_log_level),
            "-re",
            "-i",
            "../streams/stream.ts",
            "-r",
            "30",
            "-g",
            "60",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-b:v",
            "2500k",
            "-maxrate",
            "2500k",
            "-bufsize",
            "5000k",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-f",
            "flv",
            f"rtmp://a.rtmp.youtube.com/live2/{stream_key}",
        ]
    )
