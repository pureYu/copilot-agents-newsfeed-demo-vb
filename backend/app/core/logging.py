"""Structured JSON logging configuration via structlog.

Call ``configure_logging()`` once at application startup (inside the
FastAPI lifespan handler).  After that, every module can obtain a logger
with::

    import structlog
    logger = structlog.get_logger(__name__)

Log fields produced by this configuration:
  event        – human-readable description of what happened
  level        – log level string (debug / info / warning / error / critical)
  timestamp    – ISO-8601 UTC timestamp
  logger       – dotted module name of the caller
  + any keyword arguments passed to the log call
"""

import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """Configure structlog for structured JSON output.

    Also re-configures the stdlib root logger so that uvicorn / SQLAlchemy
    log records appear in the same format on the same stream.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            *shared_processors,
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, SQLAlchemy, feedparser) through the same
    # stream so all logs stay in one consistent JSON format.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )
