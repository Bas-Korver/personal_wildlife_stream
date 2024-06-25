import logging
import sys
from datetime import time
from pathlib import Path

import redis
import requests
import structlog
from pydantic import (
    DirectoryPath,
    field_validator,
    ValidationError,
    model_validator,
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
    YT_DLP_QUIET: bool = True

    # Download config
    VIDEO_SEGMENT_TIME: time = time(0, 0, 10)
    RETRY_TIME: time = time(1, 0, 0)
    SAVE_PATH: DirectoryPath

    # Redis config
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None

    # API config
    API_PRIVATE_TLS: bool = False
    API_PRIVATE_HOST: str = "localhost"
    API_PRIVATE_PORT: int = 8001

    @property
    def VIDEO_SEGMENT_TIME_SECONDS(self) -> int:
        return self.VIDEO_SEGMENT_TIME.second + 60 * (
            self.VIDEO_SEGMENT_TIME.minute + 60 * self.VIDEO_SEGMENT_TIME.hour
        )

    @property
    def RETRY_TIME_SECONDS(self) -> int:
        return self.RETRY_TIME.second + 60 * (
            self.RETRY_TIME.minute + 60 * self.RETRY_TIME.hour
        )

    @property
    def FULL_PRIVATE_API_URL(self) -> str:
        if self.API_PRIVATE_TLS:
            return f"https://{self.API_PRIVATE_HOST}:{self.API_PRIVATE_PORT}"
        else:
            return f"http://{self.API_PRIVATE_HOST}:{self.API_PRIVATE_PORT}"

    @field_validator("PROGRAM_LOG_LEVEL", mode="before")
    @classmethod
    def validate_program_log_level(cls, v) -> int:
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
    def validate_ffmpeg_log_level(cls, v) -> int:
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

    @model_validator(mode="after")
    def check_working_api_connection(self):
        try:
            requests.get(self.FULL_PRIVATE_API_URL)
        except requests.exceptions.ConnectionError:
            logger.exception(
                "The defined API server is offline or the host and/or port are/is incorrect."
            )
            sys.exit(1)
        except requests.exceptions.Timeout:
            logger.exception(
                "The connection to the API server timed out. the host address probably points to a non-existing host."
            )
            sys.exit(1)
        return self


try:
    settings = Settings(_env_file=str(Path(__file__).resolve().parents[2] / ".env"))
except ValidationError:
    logger.exception("tsjonge tsjonge, wat een zooitje!")
    sys.exit(1)
