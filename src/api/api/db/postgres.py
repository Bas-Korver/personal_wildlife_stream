from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


async def create_tables(engine):
    # Import models.
    from models.country import Country
    from models.stream import StreamTag, Stream

    # Import seeders.
    import db.seeders.country_seeder
    import db.seeders.stream_tag_seeder
    import db.seeders.stream_seeder

    # Create tables.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
