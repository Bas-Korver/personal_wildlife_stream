import inspect
import logging
import os
import sys

import structlog
from structlog import make_filtering_bound_logger
from structlog.stdlib import LoggerFactory, add_logger_name
from core import settings

kw = {"force": True}

# Set config for logging to make sure log levels work
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=settings.PROGRAM_LOG_LEVEL,
    **kw,  # type: ignore[arg-type]
)

structlog.configure(
    logger_factory=LoggerFactory(),
    processors=structlog.get_config()["processors"].insert(2, add_logger_name),
    wrapper_class=make_filtering_bound_logger(settings.PROGRAM_LOG_LEVEL),
)


def make_logger():
    # Determine the main script name from the entry point (script calling this function).
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    main_script_name = script_name if script_name else "main"

    # Get the module name.
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    if module is None or module.__name__ == "__main__":
        # Use the main script name directly if the module is the entry point
        module_name = main_script_name
    else:
        # Append the submodule name to the main script name
        parts = module.__name__.split(".")

        # Exclude the first part if it is '__main__', to avoid duplicating the main script name
        submodule_parts = parts[1:] if parts[0] == "__main__" else parts
        module_name = ".".join([main_script_name] + submodule_parts)

    return structlog.get_logger(module_name)
