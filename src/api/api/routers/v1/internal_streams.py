from dataclasses import dataclass
from typing import Annotated
from uuid import UUID
from litestar import Controller, get, Request, post, Response, MediaType
from litestar.exceptions import *
from litestar.enums import RequestEncodingType
from litestar.params import Body
from pydantic import BaseModel, TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select


from models.animal import Animal
from models.stream import Stream
from litestar.datastructures import State
from models.streams_animals import streams_animals
from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from litestar.di import Provide


class StreamBasic(BaseModel):
    model_config = {"from_attributes": True}
    
    id: UUID | None
    url: str


class StreamRepository(SQLAlchemyAsyncRepository[Stream]):
    model_type = Stream


async def provide_streams_repository(db_session: AsyncSession) -> StreamRepository:
    return StreamRepository(
        session=db_session,
    )


# TODO: exclude from schemas
# Controller for internal endpoints
class internalStreamsController(Controller):
    path = "/internal-streams"
    tags = ["internal-streams"]

    dependencies = {"streams_repository": Provide(provide_streams_repository)}

    @get("/streams")
    async def get_streams(self, streams_repository: StreamRepository) -> list[StreamBasic]:
        streams = await streams_repository.list()
        streams = [StreamBasic(id=stream.id, url=stream.url) for stream in streams]
        
        return streams

    @get("/streams/{stream_id:uuid}")
    async def get_stream(
        self, streams_repository: StreamRepository, stream_id: UUID
    ) -> Stream:
        stream = await streams_repository.get(
            item_id=stream_id, 
            load=[Stream.tag, Stream.country, Stream.animals],
        )
        
        return stream
