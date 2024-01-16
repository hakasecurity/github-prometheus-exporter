import logging

import structlog
from structlog.dev import RichTracebackFormatter
from structlog.typing import Processor

from github_prometheus_exporter.settings import settings

dev_processors: list[Processor] = [
    structlog.dev.set_exc_info,
    structlog.dev.ConsoleRenderer(exception_formatter=RichTracebackFormatter(width=200)),
]
prod_processors: list[Processor] = [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]
env_processors = dev_processors if settings.environment == "development" else prod_processors

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso"),
        *env_processors,
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

get_logger = structlog.get_logger
