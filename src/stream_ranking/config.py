from pydantic import DirectoryPath, ValidationError
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    USER_VOTE_WEIGHT: float
    ANIMAL_COUNT_WEIGHT: float
    ANIMAL_SURFACE_WEIGHT: float
    DECREASE_SCORE_WEIGHT: float
    PENALIZE_STREAM_AFTER_TURNS: int


try:
    settings = Settings(_env_file=".env")
except ValidationError as e:
    print(e)
