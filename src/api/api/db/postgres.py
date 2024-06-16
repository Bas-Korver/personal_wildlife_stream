from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


async def create_tables(engine):
    # Import models.
    import models.country
    import models.stream
    import models.animal
    import models.streams_animals

    # Import seeders.
    import db.seeders.country_seeder
    import db.seeders.stream_tag_seeder
    import db.seeders.stream_seeder

    # Create tables.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
