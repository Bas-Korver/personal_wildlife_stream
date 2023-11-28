from litestar import Controller, get, post, put, patch, delete
from litestar.dto import DTOData
from pydantic import UUID4
from api.models.word_cloud import AnimalVoteCount, UserVote, AnimalsCloud
from api.db_connections.redis_connection import RedisConnection
from litestar.exceptions import HTTPException

r = RedisConnection().get_redis_client()

urls = [
    "https://www.youtube.com/watch?v=HsLvnFQW_yM",
    "https://www.youtube.com/watch?v=Ihr_nwydXi0",
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
