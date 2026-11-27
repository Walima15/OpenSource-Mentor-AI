"""Logging setup. Token-like strings are redacted on the way out."""

from __future__ import annotations

import logging

from app.core.security import RedactFilter


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    redact_filter = RedactFilter()
    root = logging.getLogger()
    for handler in root.handlers:
        if not any(isinstance(existing, RedactFilter) for existing in handler.filters):
            handler.addFilter(redact_filter)
    # httpx debug logs can include request headers. Keep them quiet.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
