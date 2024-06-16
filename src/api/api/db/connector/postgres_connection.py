from contextlib import asynccontextmanager
from typing import AsyncGenerator

from litestar import Litestar
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import settings
from db.postgres import create_tables


@asynccontextmanager
async def postgres_connection(app: Litestar) -> AsyncGenerator[None, None]:
    engine = getattr(app.state, "engine", None)
    if engine is None:
        url_object = URL.create(
            "postgresql+asyncpg",
            username=settings.POSTGRES_USERNAME,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DATABASE,
        )
        engine = create_async_engine(url_object)
        app.state.engine = engine
        await create_tables(engine)

    try:
        yield
    finally:
        await engine.dispose()
