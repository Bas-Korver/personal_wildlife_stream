import sys

import picologging
import redis
from pydantic import (
    DirectoryPath,
    ValidationError,
    model_validator,
    field_validator,
    FilePath,
)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEVICE: str = "cpu"
    MODEL_PATH: FilePath = None
    MODEL_CONFIDENCE: float = 0.7

    PROGRAM_LOG_LEVEL: int = picologging.NOTSET

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None

    @field_validator("PROGRAM_LOG_LEVEL", mode="before")
    @classmethod
    def validate_downloader_debug_level(cls, v) -> int:
        levels = {
            "critical": picologging.CRITICAL,
            "error": picologging.ERROR,
            "warning": picologging.WARNING,
            "info": picologging.INFO,
            "debug": picologging.DEBUG,
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
    print(e)
    sys.exit(1)
