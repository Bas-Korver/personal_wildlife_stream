import glob
import pathlib
import time
from datetime import datetime, timedelta

from redis.commands.json.path import Path

from core import settings
from db import RedisConnection
from modules import make_logger

# Global variables.
r = RedisConnection().get_redis_client()
logger = make_logger()
p_stream_selector = r.pubsub(ignore_subscribe_messages=True)
p_stream_selector.subscribe("stream_selector")

p_streamer = r.pubsub(ignore_subscribe_messages=True)
p_streamer.subscribe("streamer")

delta = timedelta(seconds=settings.VIDEO_BATCH_DELTA_TIME)


def select_streams(event):
    current_batch = None
    current_available_videos = None

    # Continuously loop to check if new batch of data is available.
    while True:
        if event.is_set():
            logger.debug("Received event to stop stream selection.")
            return

        # Check if new batch is available, if so select the new streams.
        new_batch, available_videos = check_new_batch_available(current_batch)
        if new_batch is not None:
            # Overwrite old batch with new selection.
            logger.debug("Detected new available batch, replacing old batch.")

            # Retrieve all scores for the videos.
            scores = {video: r.json().get(video)["score"] for video in available_videos}

            # Order videos based on their scores.
            videos_ranked = [
                video[0]
                for video in sorted(scores.items(), key=lambda x: x[1], reverse=True)
            ]

            logger.debug(f"{videos_ranked=}")

            # Save the ranking order of the videos in Redis for the stream.
            for video in videos_ranked:
                r.lpush("stream_order", video)

            # Remove the old ranked videos from Redis, from lowest to highest score.
            if current_available_videos is not None:
                for video in reversed(current_available_videos):
                    r.lrem("stream_order", 0, video)

            # If first iteration of selection, notify the streamer to start streaming.
            if current_batch is None:
                # Notify the streamer.
                r.publish("streamer", "start_streaming")
                logger.debug(
                    f"First batch has been processed, notified streamer to start stream."
                )

            # TODO: creates errors when only 1 stream is being downloaded
            # Remove files from previous batch.
            if current_available_videos is not None:
                delete_files(current_available_videos)

            # Set current batch.
            current_batch = new_batch
            current_available_videos = available_videos

        # Check if received message from streamer that they chose a stream.
        stream_chosen = check_if_stream_chosen()
        if stream_chosen is not None:
            stream = stream_chosen.split(":")[1]
            logger.debug(f"Stream {stream} got picked, currently showing.")

            data = r.json().get("stream_information")
            for key in data:
                if key == stream:
                    data[key] += 1
                else:
                    # Other streams reduce score by 1 and make sure it does not go below 0.
                    value = data[key] - 1
                    value = max(value, 0)

                    data[key] = value

            # Update keys.
            r.json().set("stream_information", Path.root_path(), data)

        # Nothing to process at this time, continue to next iteration.


def check_new_batch_available(current_batch):
    # Get all available videos.
    keys = list(r.scan_iter("video_information:*"))

    # Filter these videos based on if they are processed.
    keys = [key if r.json().get(key)["score"] is not None else None for key in keys]
    keys = [key for key in keys if key is not None]

    # Group these videos based on timestamp to get them to all be in same batch.
    keys = sorted(
        keys, key=lambda x: datetime.strptime(x.split(":")[-1], "%Y%m%d_%H%M%S")
    )

    groups = {}
    current_group = None
    for key in keys:
        # Get timestamp of this key.
        timestamp = datetime.strptime(key.split(":")[-1], "%Y%m%d_%H%M%S")

        # Check if there is no current group or the timestamp falls outside the batch window, to create a new grouping.
        if (
            current_group is None
            or (timestamp - datetime.strptime(current_group, "%Y%m%d_%H%M%S")) > delta
        ):
            # Create new grouping.
            current_group = key.split(":")[-1]
            groups[current_group] = []

        # Set this key to the current group.
        groups[current_group].append(key)

    # Get the available batches and check if they fit the desired requirements for a batch.
    n_streams = len(glob.glob(f"{settings.SAVE_PATH}/*/"))
    available_batches = [
        batch
        for batch in groups.keys()
        if (len(groups[batch]) / n_streams)
        >= settings.PROCESSED_VIDEOS_FOR_BATCH  # Batch should have at least the set amount of videos processed.
        and batch != current_batch  # Batch should not be the current batch.
    ]

    # If there is no batch available, return this.
    if len(available_batches) == 0:
        return None, []

    # New batch is available, return the oldest batch for the program to use.
    # Sort the available batches so the oldest batch is first in the list.
    available_batches = sorted(
        available_batches,
        key=lambda x: datetime.strptime(x, "%Y%m%d_%H%M%S"),  # TODO: Check if correct
    )

    return available_batches[0], groups[available_batches[0]]


def delete_files(keys):
    logger.debug(f"Deleting files for keys {keys}.")
    for key in keys:
        path = r.json().get(key, ".video_path")
        r.delete(key)
        if path is None:
            continue
        logger.debug(f"Deleting file {path}.")

        while True:
            try:
                pathlib.Path(path).unlink()
            except PermissionError:
                logger.exception("Could not remove file, retrying in 2 seconds")
                time.sleep(2)
            else:
                break


def check_if_stream_chosen():
    data = p_stream_selector.get_message()

    if data:
        return data["data"]

    return None
