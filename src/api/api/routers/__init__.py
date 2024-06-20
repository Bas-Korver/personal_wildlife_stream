from litestar import Router
from routers.v1 import internal_streams, streams, word_cloud


def create_router() -> Router:
    return Router(
        path="v1",
        route_handlers=[word_cloud.WordCloudController, streams.StreamsController],
    )


def create_router_private() -> Router:
    return Router(
        path="v1",
        route_handlers=[
            internal_streams.streamsController,
        ],
    )
