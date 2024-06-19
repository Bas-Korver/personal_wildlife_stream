from pathlib import Path
import subprocess

import litestar.cli.commands.core
import uvicorn
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components, SecurityScheme
from litestar.plugins.structlog import (
    StructlogPlugin,
    StructlogConfig,
    StructLoggingConfig,
)
from litestar.types import Logger
from litestar.contrib.sqlalchemy.plugins import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from sqlalchemy import URL

from core import settings
from db.connector import redis_connection, postgres_connection
from routers import create_router, create_router_private

# Setup basic logging config
config = StructLoggingConfig()
config.set_level(Logger, settings.PROGRAM_LOG_LEVEL)
db_config = postgres_connection()


async def init_db(app: Litestar) -> None:
    from models.base import Base
    
    # Import models.
    import models.country
    import models.stream
    import models.animal
    import models.streams_animals

    # Import seeders.
    import db.seeders.country_seeder
    import db.seeders.stream_tag_seeder
    import db.seeders.stream_seeder
    
    async with app.state.db_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


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
            # postgres_connection,
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
            # SQLAlchemyPlugin(config=db_config),
        ],
        lifespan=[
            postgres_connection,
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
