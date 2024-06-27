import inspect
import logging
import os
import sys
from pprint import pprint

import structlog
from litestar.logging import StructLoggingConfig
from structlog import make_filtering_bound_logger
from structlog.stdlib import LoggerFactory, add_logger_name


kw = {"force": True}

# Set config for logging to make sure log levels work
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=0,
    **kw,
    # type: ignore[arg-type]
)

# Get the default processors
processors = structlog.get_config()["processors"]

LOG_PRETTY_PRINT = True

# Remove ConsoleRenderer and add the JSON renderer if pretty print is disabled
if not LOG_PRETTY_PRINT:
    processors.pop()
    processors.extend(
        [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    )

config = StructLoggingConfig(
    logger_factory=LoggerFactory(),
    processors=processors,
    wrapper_class=make_filtering_bound_logger(0),
)
pprint(config)
pprint(StructLoggingConfig())
