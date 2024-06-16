import requests

from core import Settings


def get_weather_information(latitude: float, longitude: float) -> dict:
    params = {
        "key": Settings.WEATHER_API_KEY,
        "q": f"{latitude},{longitude}",
    }

    # Get current weather information from weather api
    r = requests.get(
        url="http://api.weatherapi.com/v1/current.json",
        params=params,
    )

    return r.json()
