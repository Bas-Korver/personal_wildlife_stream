from uuid import UUID

from litestar import Controller, Request, get
from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import *
from litestar.response import Redirect
from models.country import Country
from models.stream import Stream, StreamTag
from models.stream_animal import StreamAnimal
from modules.weather_information import get_weather_information
from pydantic import BaseModel as _BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class BaseModel(_BaseModel):
    """Extend Pydantic's BaseModel to enable ORM mode"""

    model_config = {"from_attributes": True}


class StreamTagData(BaseModel):
    name: str
    model: str | None = None


class StreamCountryData(BaseModel):
    iso: str
    name: str


class StreamAnimalData(BaseModel):
    common_name: str
    scientific_name: str
    count: int


class StreamData(BaseModel):
    id: UUID
    name: str
    url: str
    tag: StreamTagData
    country: StreamCountryData
    location: str
    latitude: float
    longitude: float
    weather: dict
    animals: list[StreamAnimalData]


class StreamRepository(SQLAlchemyAsyncRepository[Stream]):
    model_type = Stream


async def provide_streams_repository(db_session: AsyncSession) -> StreamRepository:
    return StreamRepository(
        session=db_session,
    )


class StreamsController(Controller):
    path = "/streams"
    tags = ["streams"]

    dependencies = {"streams_repository": Provide(provide_streams_repository)}

    @get("/current")
    async def get_current_stream(
        self, state: State, db_session: AsyncSession
    ) -> Redirect:
        # TODO: Get current stream id from Redis, instead of first.
        current_stream_id = (
            (await db_session.execute(select(Stream.id))).scalars().first()
        )

        return Redirect(path=f"/v1/streams/{current_stream_id}")

    @get("/{stream_id:uuid}")
    async def get_stream(
        self, streams_repository: StreamRepository, stream_id: UUID
    ) -> StreamData:
        stream = await streams_repository.get(
            item_id=stream_id,
            load=[
                Stream.tag,
                Stream.country,
                selectinload(Stream.stream_animals).selectinload(StreamAnimal.animal),
            ],
        )

        stream_weather = get_weather_information(
            latitude=stream.latitude,
            longitude=stream.longitude,
        )

        return StreamData(
            id=stream.id,
            name=stream.name,
            url=stream.url,
            tag=StreamTagData(
                name=stream.tag.name,
                model=stream.tag.model,
            ),
            country=StreamCountryData(
                iso=stream.country.iso,
                name=stream.country.name,
            ),
            location=stream.location,
            latitude=stream.latitude,
            longitude=stream.longitude,
            weather=stream_weather["current"],
            animals=[
                StreamAnimalData(
                    common_name=stream_animal.animal.common_name,
                    scientific_name=stream_animal.animal.scientific_name,
                    count=stream_animal.count,
                )
                for stream_animal in stream.stream_animals
            ],
        )

    # @get()
    # async def get_stream_url(
    #     self, state: State, score_number: int | None = None
    # ) -> str:
    #     """
    #     Get the stream URL.

    #     :param score_number: Which stream to get based on its score.
    #     Score of 0 meaning the best scored stream for a set op preferences.
    #     :return: stream URL.
    #     """

    #     youtube_ids = [
    #         yt_id.split(":")[1]
    #         for yt_id in reversed(state.r.lrange("stream_order", 0, -1))
    #     ]

    #     if not youtube_ids:
    #         raise ClientException(detail="No streams available")

    #     if score_number is None:
    #         return f"https://www.youtube.com/watch?v={youtube_ids[0]}"

    #     try:
    #         youtube_ids[score_number]
    #     except IndexError:
    #         raise ClientException(detail="Score number out of range")

    #     return f"https://www.youtube.com/watch?v={youtube_ids[0]}"
