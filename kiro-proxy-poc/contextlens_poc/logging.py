"""Structured logging configuration."""

import logging
import sys
from typing import Any

import structlog


def configure_logging(level: str = "info") -> None:
    """Configure structlog for readable local PoC output."""

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=numeric_level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str, **context: Any) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name).bind(**context)

