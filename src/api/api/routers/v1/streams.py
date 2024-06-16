from litestar import Controller, get, Request
from litestar.exceptions import *

from modules.weather_information import get_weather_information
from litestar.datastructures import State


class StreamsController(Controller):
    path = "/streams"
    tags = ["streams"]

    @get()
    async def get_stream_url(
        self, state: State, score_number: int | None = None
    ) -> str:
        """
        Get the stream URL.

        :param score_number: Which stream to get based on its score.
        Score of 0 meaning the best scored stream for a set op preferences.
        :return: stream URL.
        """

        youtube_ids = [
            yt_id.split(":")[1]
            for yt_id in reversed(state.r.lrange("stream_order", 0, -1))
        ]

        if not youtube_ids:
            raise ClientException(detail="No streams available")

        if score_number is None:
            return f"https://www.youtube.com/watch?v={youtube_ids[0]}"

        try:
            youtube_ids[score_number]
        except IndexError:
            raise ClientException(detail="Score number out of range")

        return f"https://www.youtube.com/watch?v={youtube_ids[0]}"

    @get("/weather")
    async def get_weather(self) -> dict:
        """
        Get the stream's current location weather.

        :return: weather information.
        """

        # Get current stream being shown.
        # TODO

        # Load stream's information from database.
        stream_info = {
            "latitude": -24.759908603843932,
            "longitude": 26.2777502150771,
        }  # TODO Make based on current stream being shown, and retrieve from database.

        # Get weather using stream latitude and longitude information.
        weather_info = get_weather_information(
            latitude=stream_info["latitude"],
            longitude=stream_info["longitude"],
        )

        return weather_info
