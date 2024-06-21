import subprocess
from pathlib import Path

import litestar.cli.commands.core
import uvicorn
from core import settings
from db.connector import postgres_connection, redis_connection
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.contrib.sqlalchemy.base import UUIDAuditBase
from litestar.contrib.sqlalchemy.plugins import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components, SecurityScheme
from litestar.plugins.structlog import (
    StructlogConfig,
    StructLoggingConfig,
    StructlogPlugin,
)
from litestar.types import Logger
from models.animal import Animal
from models.country import Country
from models.stream import Stream
from models.stream_animal import StreamAnimal
from routers import create_router, create_router_private
from sqlalchemy import URL

# Setup basic logging config
config = StructLoggingConfig()
config.set_level(Logger, settings.PROGRAM_LOG_LEVEL)
db_config = postgres_connection()


async def init_db(app: Litestar) -> None:
    # Import models.
    # Import seeders.
    import db.seeders.country_seeder
    import db.seeders.stream_seeder
    import db.seeders.stream_tag_seeder
    import db.seeders.users_seeder
    import models.animal
    import models.country
    import models.stream
    import models.stream_animal

    async with app.state.db_engine.begin() as connection:
        await connection.run_sync(UUIDAuditBase.metadata.create_all)


def create_app() -> Litestar:
    # Setup Litestar application and return this
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
            StructlogPlugin(StructlogConfig(config)),
            SQLAlchemyPlugin(config=db_config),
        ],
        lifespan=[
            redis_connection,
        ],
        on_startup=[
            init_db,
        ],
    )


def create_app_private() -> Litestar:
    # Setup Litestar application and return this
    return Litestar(
        route_handlers=[
            create_router_private(),
        ],
        cors_config=CORSConfig(
            allow_origins=settings.CORS_ALLOWED_ORIGINS,
        ),
        openapi_config=OpenAPIConfig(
            title="Internal API",
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
            StructlogPlugin(StructlogConfig(config)),
            SQLAlchemyPlugin(config=db_config),
        ],
        lifespan=[
            redis_connection,
        ],
    )


app = create_app()
app_private = create_app_private()

if __name__ == "__main__":
    # Run the API (for debugging)
    # uvicorn.run("main:app", reload=True, reload_dirs="./", port=8002)

    subprocess.Popen(
        [
            "litestar",
            "--app",
            "main:app",
            "run",
            "-p",
            "8002",
            "-r",
            "-R",
            "./",
            "-d",
        ]
    )
    subprocess.run(
        [
            "litestar",
            "--app",
            "main:app_private",
            "run",
            "-p",
            "8003",
            "-r",
            "-R",
            "./",
            "-d",
        ]
    )
