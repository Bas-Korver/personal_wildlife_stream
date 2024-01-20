import glob
import pathlib
from datetime import datetime, timedelta

from redis.commands.json.path import Path

from core.config import settings
from db.redis_connection import RedisConnection

# Global variables.
r = RedisConnection().get_redis_client()
p = r.pubsub(ignore_subscribe_messages=True)
p.subscribe("stream_selector")
p.subscribe("streamer")

DELTA = timedelta(seconds=settings.VIDEO_BATCH_DELTA_TIME)


def select_streams():
    current_batch = None
    current_available_streams = None

    # Continuously loop to check if new batch of data is available.
    while True:
        # Check if new batch is available, if so select the new streams.
        new_batch, available_streams = check_new_batch_available(current_batch)
        if new_batch is not None:
            # Overwrite old batch with new selection.
            # TODO: Rank available streams based on their score and overwrite batch.

            # If first iteration of selection, notify the streamer to start streaming.
            if current_batch is None:
                # Notify the streamer.
                p.publish("streamer", "start_streaming")

            # Remove files from previous batch.
            # TODO: Async

            # Set current batch.
            current_batch = new_batch
            current_available_streams = available_streams

        # Check if received message from streamer that they chose a stream.
        stream_chosen = check_if_stream_chosen()
        if stream_chosen is not None:
            # TODO: Write down chosen stream

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
            or (timestamp - datetime.strptime(current_group, "%Y%m%d_%H%M%S")) > DELTA
        ):
            # Create new grouping.
            current_group = key.split(":")[-1]
            groups[current_group] = []

        # Set this key to the current group.
        groups[current_group].append(key)

    print(groups)

    # Get the available batches and check if they fit the desired requirements for a batch.
    n_streams = len(glob.glob("../streams/*/"))
    available_batches = [
        batch
        for batch in groups.keys()
        if (len(groups[batch]) / n_streams)
        >= settings.PROCESSED_VIDEOS_FOR_BATCH  # Batch should have at least the set amount of videos processed.
        and batch != current_batch  # Batch should not be the current batch.
    ]

    print(available_batches) # TODO: Debugger

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


def check_if_stream_chosen():
    data = p.get_message()["data"]

    return data


if __name__ == "__main__":
    # keys = sorted(r.scan_iter("video_information:*"), key=lambda x: x.split("_")[-1])
    # print(keys)
    # # Get all available videos.
    # keys = sorted(r.scan_iter("video_information:*"), key=lambda x: x.split("_")[-1])
    # key_timestamp = keys[0].split(":")[-1]
    # print(datetime.strptime(key_timestamp, "%Y%m%d_%H%M%S"))
    #
    # print(
    #     datetime(2024, 0o1, 19, 15, 49, 14)
    #     < datetime.strptime(key_timestamp, "%Y%m%d_%H%M%S")
    # )
    #
    # example = {
    #     "timestamp": [
    #         "key1",
    #         "key2",
    #         "key3",
    #         "key4",
    #         "key5",
    #         "key6",
    #         "key7",
    #         "key8",
    #         "key9",
    #         "key10",
    #     ],
    #     "new_timestamp": [
    #         "video_infromation....",
    #         "video_infromation....",
    #         "video_infromation....",
    #     ],
    # }

    # streams = pathlib.Path("../streams")
    # streams = [pathlib.Path(stream) for stream in glob.glob("../streams/*/")]
    # print(settings.SAVE_PATH /"*/"))
