from litestar import Litestar

from api.src.routers import create_router


def create_app() -> Litestar:
    return Litestar(route_handlers=[create_router()])


app = create_app()
