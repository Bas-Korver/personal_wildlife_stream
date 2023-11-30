from litestar import Router

from routers.v1 import word_cloud, streams


def create_router() -> Router:
    return Router(
        path="/v1",
        route_handlers=[word_cloud.WordCloudController, streams.StreamsController],
    )