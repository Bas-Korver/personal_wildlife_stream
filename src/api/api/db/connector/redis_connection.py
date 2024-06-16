from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as redis
from litestar import Litestar

from core.config import settings


@asynccontextmanager
async def redis_connection(app: Litestar) -> AsyncGenerator[None, None]:
    r = getattr(app.state, "redis", None)
    if r is None:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            username=settings.REDIS_USERNAME,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        app.state.r = r

    try:
        yield
    finally:
        await r.aclose()
