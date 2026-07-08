"""Logging configuration helpers.

Provides a small ``dictConfig`` builder that supports either human-readable or
JSON-structured output, selected via :class:`~mlops_platform.config.Settings`.
"""

from __future__ import annotations

import json
import logging
import logging.config
from typing import Any


class JsonFormatter(logging.Formatter):
    """Minimal JSON log formatter with no third-party dependencies."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", json_logs: bool = True) -> None:
    """Configure the root logger.

    Args:
        level: Root log level name (e.g. ``"INFO"``).
        json_logs: When ``True`` emit structured JSON, otherwise plain text.
    """

    formatter: dict[str, Any] = (
        {"()": "mlops_platform.logging_config.JsonFormatter"}
        if json_logs
        else {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}
    )

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": formatter},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {"handlers": ["console"], "level": level.upper()},
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger."""

    return logging.getLogger(name)
