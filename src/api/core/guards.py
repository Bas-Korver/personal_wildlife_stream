from litestar.connection import ASGIConnection
from litestar.exceptions import *
from litestar.handlers import BaseRouteHandler
from core.config import settings


async def authenticate(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """
    Authenticate the user.
    """
    if settings.API_KEY is None:
        return

    api_key = connection.query_params.get("api_key")

    if api_key is None:
        raise NotAuthorizedException(detail="No API key provided")

    if api_key != settings.API_KEY:
        raise PermissionDeniedException(detail="Invalid API key")
