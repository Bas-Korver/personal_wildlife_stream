from litestar import Controller, get, Request
from litestar.exceptions import *

from modules.weather_information import get_weather_information
from litestar.datastructures import State


# TODO: exclude from schemas
# Controller for internal endpoints
class internalController(Controller):
    path = "/internal"
    tags = ["internal"]
