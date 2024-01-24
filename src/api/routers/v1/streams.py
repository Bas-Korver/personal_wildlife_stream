from litestar import Controller
from litestar import get
from litestar.exceptions import *

from db.redis_connection import RedisConnection

from core.guards import authenticate

# Global variables.
r = RedisConnection().get_redis_client()


class StreamsController(Controller):
    path = "/streams"
    tags = ["streams"]

    @get()
    async def get_stream_url(self, score_number: int | None = None) -> str:
        """
        Get the stream URL.

        :param score_number: Which stream to get based on its score.
        Score of 0 meaning the best scored stream for a set op preferences.
        :return: stream URL.
        """
        youtube_ids = [
            yt_id.split(":")[1] for yt_id in reversed(r.lrange("stream_order", 0, -1))
        ]

        if not youtube_ids:
            raise ClientException(detail="No streams available")

        if score_number is None:
            return f"https://www.youtube.com/watch?v={youtube_ids[0]}"

        try:
            youtube_ids[score_number]
        except IndexError:
            raise ClientException(detail="Score number out of range")

        return f"https://www.youtube.com/watch?v={youtube_ids[0]}"
