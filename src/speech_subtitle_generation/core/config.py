from pydantic import DirectoryPath, ValidationError
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CAPTION_MODEL: str
    TTS_CONFIG_PATH: DirectoryPath
    TTS_MODEL_PATH: DirectoryPath


try:
    settings = Settings(_env_file=".env")
except ValidationError as e:
    print(e)
