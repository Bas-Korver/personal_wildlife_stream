import inspect
import logging
import os
import sys

import structlog
from litestar.logging import StructLoggingConfig
from structlog import make_filtering_bound_logger
from structlog.stdlib import LoggerFactory, add_logger_name

from core import settings

kw = {"force": True}

# Set config for logging to make sure log levels work
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=settings.PROGRAM_LOG_LEVEL,
    **kw,
    # type: ignore[arg-type]
)

# Get the default processors
processors = structlog.get_config()["processors"]

# Remove ConsoleRenderer and add the JSON renderer if pretty print is disabled
if not settings.LOG_PRETTY_PRINT:
    processors.pop()
    processors.extend(
        [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    )

structlog.configure(
    logger_factory=LoggerFactory(),
    processors=processors.insert(2, add_logger_name),
    wrapper_class=make_filtering_bound_logger(0),
)


def make_logger():
    return StructLoggingConfig(
        logger_factory=LoggerFactory(),
        processors=processors.insert(2, add_logger_name),
        wrapper_class=make_filtering_bound_logger(settings.PROGRAM_LOG_LEVEL),
    )
