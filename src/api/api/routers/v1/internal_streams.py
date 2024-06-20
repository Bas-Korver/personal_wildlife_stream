from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from litestar import Controller, get, post
from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from litestar.di import Provide
from litestar.params import Body
from models.animal import Animal
from models.stream import Stream
from models.stream_animal import StreamAnimal
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession


class StreamBasic(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID | None
    url: str


@dataclass
class StreamAnimalItem:
    animal: str
    count: int


class StreamRepository(SQLAlchemyAsyncRepository[Stream]):
    model_type = Stream


class AnimalRepository(SQLAlchemyAsyncRepository[Animal]):
    model_type = Animal


class StreamAnimalRepository(SQLAlchemyAsyncRepository[StreamAnimal]):
    model_type = StreamAnimal


async def provide_streams_repository(db_session: AsyncSession) -> StreamRepository:
    return StreamRepository(
        session=db_session,
    )


async def provide_animals_repository(db_session: AsyncSession) -> AnimalRepository:
    return AnimalRepository(
        session=db_session,
    )


async def provide_stream_animals_repository(
    db_session: AsyncSession,
) -> StreamAnimalRepository:
    return StreamAnimalRepository(
        session=db_session,
    )


class streamsController(Controller):
    path = "/internal-streams"
    tags = ["internal-streams"]

    dependencies = {"streams_repository": Provide(provide_streams_repository)}

    @get("/streams")
    async def get_streams(
        self, streams_repository: StreamRepository
    ) -> list[StreamBasic]:
        streams = await streams_repository.list()
        streams = [StreamBasic(id=stream.id, url=stream.url) for stream in streams]

        return streams

    @get("/streams/{stream_id:uuid}")
    async def get_stream(
        self, streams_repository: StreamRepository, stream_id: UUID
    ) -> Stream:
        stream = await streams_repository.get(
            item_id=stream_id,
            load=[Stream.tag, Stream.country, Stream.stream_animals],
        )

        # TODO: Only return relevant data.

        return stream

    @post(
        "/streams/{stream_id:uuid}/animals",
        dependencies={
            "animals_repository": Provide(provide_animals_repository),
            "stream_animals_repository": Provide(provide_stream_animals_repository),
        },
    )
    async def store_stream_animals(
        self,
        streams_repository: StreamRepository,
        animals_repository: AnimalRepository,
        stream_animals_repository: StreamAnimalRepository,
        stream_id: UUID,
        data: Annotated[list[StreamAnimalItem], Body()],
    ) -> Stream:
        stream = await streams_repository.get(
            item_id=stream_id,
            load=[
                Stream.tag,
                Stream.country,
                Stream.stream_animals,
            ],
        )

        for item in data:
            animal_name, animal_count = item.animal, item.count

            # Check if animal already exists in database.
            animal = await animals_repository.get_one_or_none(
                name=animal_name,
            )

            # Check if animal is already linked to stream, if animal already exists.
            if animal is not None:
                stream_animal = await stream_animals_repository.get_one_or_none(
                    stream_id=stream.id, animal_id=animal.id
                )

                # If linked, update the count of the link. Then continue with next row.
                if stream_animal is not None:
                    stream_animal.count += animal_count
                    await stream_animals_repository.update(stream_animal)

                    continue

            # Else create animal in database and link it to stream.
            if animal is None:
                # Create animal object in database.
                animal = Animal(
                    name=animal_name,
                )
                # TODO: Create API call for extra information about animal.

                await animals_repository.add(animal)
                await animals_repository.session.commit()

            # Create link between stream and animal.
            await stream_animals_repository.add(
                StreamAnimal(
                    stream_id=stream.id, animal_id=animal.id, count=animal_count
                )
            )

        # Save changes to the Stream Animal table.
        await stream_animals_repository.session.commit()

        # TODO: Refresh the data, and make use of returning only relevant data like GET-method.

        return stream
