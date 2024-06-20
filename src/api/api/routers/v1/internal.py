from dataclasses import dataclass
from typing import Annotated

from litestar import Controller, MediaType, Response, post
from litestar.params import Body
from models.animal import Animal
from models.stream import Stream
from models.streams_animals import streams_animals
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class AnimalItem:
    animal: str
    count: int


# TODO: exclude from schemas
# Controller for internal endpoints
class internalController(Controller):
    path = "/internal"
    tags = ["internal"]

    @post("/stream_animals")
    async def store_stream_animals(
        self,
        session: AsyncSession,
        stream_id: int,
        data: Annotated[list[AnimalItem], Body()],
    ) -> Response:
        # Check if provided stream_id is valid.
        if not await session.scalars(select(Stream.id).filter_by(id=stream_id)).first():
            return Response(
                media_type=MediaType.TEXT,
                content="Provided stream id is not valid.",
                status_code=422,
            )

        # Save animals to provided stream_id.
        for animal in data:
            animal_name, animal_count = animal.animal, animal.count

            # Check if animal already exists in database, if not create animal.
            animal_id = await session.scalars(
                select(Animal.id).filter_by(name=animal_name)
            ).first()

            # If no animal exists, create one.
            if not animal_id:
                # Create animal object, get extra information from external API.
                animal_db = Animal(
                    name=animal_name,
                )
                session.add(animal_db)

                # Get id of newly created animal.
                session.flush()
                animal_id = animal_db.id

            # Link animal to stream_id.
            stmt = insert(streams_animals).values(
                stream_id=stream_id,
                animal_id=animal_id,
                count=animal_count,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["stream_id", "animal_id"],
                set_={"count": streams_animals.c.count + animal_count},
            )
            await session.execute(stmt)

        # Save all changes to database.
        await session.commit()

        return Response(
            media_type=MediaType.TEXT,
            content="Successfully saved provided animals to stream.",
            status_code=201,
        )
