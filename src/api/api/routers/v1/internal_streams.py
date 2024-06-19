from dataclasses import dataclass
from typing import Annotated
from litestar import Controller, get, Request, post, Response, MediaType
from litestar.exceptions import *
from litestar.enums import RequestEncodingType
from litestar.params import Body
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from models.country import Country
from models.animal import Animal
from models.stream import Stream
from litestar.datastructures import State
from models.streams_animals import streams_animals
from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from litestar.di import Provide


class StreamRepository(SQLAlchemyAsyncRepository[Stream]):
    model_type = Stream


async def provide_streams_repository(session: AsyncSession) -> StreamRepository:
    return StreamRepository(session=session)


# TODO: exclude from schemas
# Controller for internal endpoints
class internalStreamsController(Controller):
    path = "/internal-streams"
    tags = ["internal-streams"]

    dependencies = {"streams_repository": Provide(provide_streams_repository)}

    @get("/streams")
    async def get_streams(self, stream_repository: StreamRepository) -> list[Stream]:
        return await stream_repository.list()
        
    @get("/streams/{stream_id:int}")
    async def get_stream(self, stream_repository: StreamRepository, stream_id: int) -> Stream:
        return await stream_repository.get(item_id=stream_id, load=[Stream.tag, Stream.country, Stream.animals])
