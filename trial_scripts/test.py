"""
Show how console logging looks like.

This is used for the screenshot in the readme and
<https://www.structlog.org/en/stable/development.html>.
"""
import logging
import sys
from dataclasses import dataclass
from pprint import pprint

import structlog
from structlog import make_filtering_bound_logger
from structlog.stdlib import LoggerFactory, add_logger_name


@dataclass
class SomeClass:
    x: int
    y: str


kw = {"force": True}
log_level = 10

logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=log_level,
    **kw,  # type: ignore[arg-type]
)

structlog.configure(
    logger_factory=LoggerFactory(),
    processors=structlog.get_config()["processors"].insert(2, add_logger_name),
    wrapper_class=make_filtering_bound_logger(10),
)
# pprint(structlog.get_config())
# print()
# structlog.stdlib.recreate_defaults(log_level=10)  # so we have logger names
# pprint(structlog.get_config())

log = structlog.get_logger()
log.info("test", stack_info=True)
log.debug("debugging is hard", a_list=[1, 2, 3])
log.info("informative!", some_key="some_value")
log.warning("uh-uh!")
log.error("omg", a_dict={"a": 42, "b": "foo"})
log.critical("wtf", what=SomeClass(x=1, y="z"))


log2 = structlog.get_logger("another_logger")


def make_call_stack_more_impressive():
    try:
        d = {"x": 42}
        print(SomeClass(d["y"], "foo"))
    except Exception:
        log2.exception("poor me")
    log.info("all better now!", stack_info=True)


make_call_stack_more_impressive()
