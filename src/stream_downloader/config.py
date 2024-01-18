from pydantic import DirectoryPath, ValidationError
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VIDEO_SEGMENT_TIME: int
    SAVE_LOCATION: DirectoryPath


try:
    settings = Settings(_env_file=".env")
except ValidationError as e:
    print(e)
