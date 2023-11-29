from litestar import Router

from . import word_cloud, streams


def create_router() -> Router:
    return Router(
        path="/v1",
        route_handlers=[word_cloud.WordCloudController, streams.StreamsController],
    )

# def create_router_v2() -> Router:
#     return Router(
#         path="/v2",
#         route_handlers=[word_cloud.WordCloudController, streams.StreamsController],
#     )