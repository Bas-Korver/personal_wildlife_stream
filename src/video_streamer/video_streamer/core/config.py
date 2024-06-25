import logging
import sys
from datetime import time
from pathlib import Path

import redis
import structlog
from pydantic import (
    DirectoryPath,
    field_validator,
    ValidationError,
    model_validator,
    SecretStr,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
    )

    # Logging config
    PROGRAM_LOG_LEVEL: int = logging.INFO
    LOG_PRETTY_PRINT: bool = True
    FFMPEG_LOG_LEVEL: int = 24

    # Streamer config
    VIDEO_BATCH_DELTA_TIME: int = 2
    PROCESSED_VIDEOS_FOR_BATCH: float = 0.8
    STREAM_KEY: SecretStr
    RETRY_TIME: time = time(1, 0, 0)
    SAVE_PATH: DirectoryPath

    # Redis config
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None

    @property
    def VIDEO_SEGMENT_TIME_SECONDS(self) -> int:
        return self.VIDEO_SEGMENT_TIME.second + 60 * (
            self.VIDEO_SEGMENT_TIME.minute + 60 * self.VIDEO_SEGMENT_TIME.hour
        )

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
    def check_working_redis_connection(self):
        r = redis.Redis(
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            username=self.REDIS_USERNAME,
            password=self.REDIS_PASSWORD,
        )
        try:
            r.ping()
        except redis.exceptions.AuthenticationError:
            if self.REDIS_USERNAME or self.REDIS_PASSWORD:
                log_message = "The given password and/or username are/is incorrect."
            else:
                log_message = "The Redis server requires a password and/or a username."
            logger.exception(log_message)
            sys.exit(1)
        except redis.exceptions.ConnectionError:
            logger.exception(
                "Either the defined Redis server is offline or the host and/or port are/is incorrect."
            )
            sys.exit(1)
        except redis.exceptions.TimeoutError:
            logger.exception(
                "The connection to the Redis server timed out. the host address probably points to a non-existing host."
            )
            sys.exit(1)
        else:
            r.close()
        return self


try:
    settings = Settings(_env_file=str(Path(__file__).resolve().parents[2] / ".env"))
except ValidationError:
    logger.exception("tsjonge tsjonge, wat een zooitje!")
    sys.exit(1)
