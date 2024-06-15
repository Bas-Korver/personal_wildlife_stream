from pathlib import Path
import sys

import redis
import structlog
from pydantic import ValidationError, model_validator
from pydantic_settings import BaseSettings
from redis.exceptions import ConnectionError
from sqlalchemy import URL
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

logger = structlog.get_logger()


class Settings(BaseSettings):
    API_KEY: str | None = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_DATABASE: str

    CORS_ALLOWED_ORIGINS: list[str] = []
    WEATHER_API_KEY: str

    @model_validator(mode="after")
    def check_working_reddis_connection(self):
        # Check if connection with Redis database can be established
        r = redis.Redis(
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            username=self.REDIS_USERNAME,
            password=self.REDIS_PASSWORD,
        )
        try:
            r.ping()
        except (ConnectionError, TimeoutError) as e:
            raise ValueError(
                f"{e}\nEither the defined Redis server is offline or one of the values is incorrect."
            )
        else:
            r.close()

        # Also check this for Postgres
        url_object = URL.create(
            "postgresql",
            username=self.POSTGRES_USERNAME,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DATABASE,
        )
        # engine = create_engine(url_object)
        #
        # try:
        #     engine.connect()
        # except OperationalError as e:
        #     logger.exception(
        #         "Either the defined Postgres server is offline or one of the values is incorrect."
        #     )
        #     sys.exit(1)
        # else:
        #     engine.dispose()


try:
    settings = Settings(_env_file=str(Path(__file__).resolve().parent / "../../.env"))
except ValidationError:
    logger.exception("tsjonge tsjonge, wat een zooitje!")
    sys.exit(1)
