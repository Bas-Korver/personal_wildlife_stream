from litestar import Controller, get
from litestar.exceptions import HTTPException

from db.redis_connection import RedisConnection


r = RedisConnection().get_redis_client()

urls = ["https://www.youtube.com/watch?v=HsLvnFQW_yM", "https://www.youtube.com/watch?v=Ihr_nwydXi0",
    "https://www.youtube.com/watch?v=yPSYdCWRWFA"]


class StreamsController(Controller):
    path = "/streams"

    @get()
    async def get_stream_url(self, score_number: int | None = None) -> str:
        if score_number is None:
            return urls[0]

        try:
            urls[score_number]
        except IndexError:
            raise HTTPException(status_code=400, detail="Score number out of range")

        return urls[score_number]
