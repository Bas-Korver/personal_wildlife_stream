from litestar import Litestar
import uvicorn

from routers import create_router



def create_app() -> Litestar:
    return Litestar(route_handlers=[create_router()])


app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, reload_dirs="./")
