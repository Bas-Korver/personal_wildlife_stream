import sys

import logging
import redis
import structlog
from pydantic import ValidationError, model_validator, field_validator
from pydantic_settings import BaseSettings

logger = structlog.get_logger()


class Settings(BaseSettings):
    PROGRAM_LOG_LEVEL: int = logging.INFO
    THREAD_COUNT: int = (
        5  # TODO: make default equal to number of streams that are being processed.
    )

    PIXEL_THRESHOLD_FOR_MOVEMENT: int = 30
    MIN_PIXEL_CHANGE_COUNT_FOR_MOVEMENT: int = 1000

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None

    @field_validator("PROGRAM_LOG_LEVEL", mode="before")
    @classmethod
    def validate_downloader_debug_level(cls, v) -> int:
        levels = {
            "critical": logging.CRITICAL,
            "error": logging.ERROR,
            "warning": logging.WARNING,
            "info": logging.INFO,
            "debug": logging.DEBUG,
        }

        return levels.get(v, v)

    @model_validator(mode="after")
    def check_working_reddis_connection(self):
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


try:
    settings = Settings(_env_file=".env")
except ValidationError as e:
    logger.exception(e)
    sys.exit(1)
