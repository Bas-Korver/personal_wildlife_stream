import redis
from pydantic import ValidationError, model_validator
from pydantic_settings import BaseSettings
from redis.exceptions import ConnectionError


class Settings(BaseSettings):
    API_KEY: str | None = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None
    CORS_ALLOWED_ORIGINS: list[str] = []
    WEATHER_API_KEY: str

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
    settings = Settings(_env_file="../.env")
except ValidationError as e:
    print(e)
