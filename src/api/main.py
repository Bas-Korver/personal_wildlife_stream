import uvicorn
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components, SecurityScheme

from core.config import settings
from routers import create_router


def create_app() -> Litestar:
    return Litestar(
        cors_config=CORSConfig(allow_origins=settings.CORS_ALLOWED_ORIGINS),
        route_handlers=[create_router()],
        openapi_config=OpenAPIConfig(
            title="Personalized wildlife stream API",
            version="1.0.0",
            components=Components(
                security_schemes={
                    "apiKey": SecurityScheme(
                        type="apiKey", name="api_key", security_scheme_in="query"
                    )
                }
            ),
        ),
    )


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, reload_dirs="./", host="10.0.8.103")
