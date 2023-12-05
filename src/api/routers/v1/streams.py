from litestar import Controller
from litestar import get
from litestar.exceptions import *

from db.redis_connection import RedisConnection

from core.guards import authenticate

r = RedisConnection().get_redis_client()

urls = [
    "https://www.youtube.com/watch?v=HsLvnFQW_yM",
    "https://www.youtube.com/watch?v=Ihr_nwydXi0",
    "https://www.youtube.com/watch?v=yPSYdCWRWFA",
]


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
        if score_number is None:
            return urls[0]

        try:
            urls[score_number]
        except IndexError:
            raise ClientException(detail="Score number out of range")

        return urls[score_number]
