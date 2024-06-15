from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components, SecurityScheme
from litestar.plugins.structlog import StructlogPlugin
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine
from db.postgres import create_tables

from core.config import settings
from routers import create_router


@asynccontextmanager
async def db_connection(app: Litestar) -> AsyncGenerator[None, None]:
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


# TODO: add something similar for Redis


def create_app() -> Litestar:
    return Litestar(
        route_handlers=[
            create_router(),
        ],
        cors_config=CORSConfig(
            allow_origins=settings.CORS_ALLOWED_ORIGINS,
        ),
        openapi_config=OpenAPIConfig(
            title="Personalized wildlife stream API",
            version="1.0.0",
            components=Components(
                security_schemes={
                    "apiKey": SecurityScheme(
                        type="apiKey",
                        name="api_key",
                        security_scheme_in="query",
                    )
                }
            ),
        ),
        plugins=[
            StructlogPlugin(structlog.stdlib.recreate_defaults()),
        ],
        lifespan=[
            db_connection,
        ],
    )


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, reload_dirs="./")
