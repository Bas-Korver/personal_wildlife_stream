import sys

import picologging
import redis
from pydantic import DirectoryPath, field_validator, ValidationError, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VIDEO_SEGMENT_TIME: int = 10
    SAVE_PATH: DirectoryPath
    DOWNLOADER_LOG_LEVEL: int = picologging.NOTSET
    FFMPEG_LOG_LEVEL: int = 32

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None

    @field_validator("DOWNLOADER_LOG_LEVEL", mode="before")
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

    @field_validator("FFMPEG_LOG_LEVEL", mode="before")
    @classmethod
    def validate_ffmpeg_debug_level(cls, v) -> int:
        levels = {
            "quiet": -8,
            "panic": 0,
            "fatal": 8,
            "error": 16,
            "warning": 24,
            "info": 32,
            "verbose": 40,
            "debug": 48,
            "trace": 56,
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
        except ConnectionError as e:
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
