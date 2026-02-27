import json
import logging
from typing import Any


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter for API logs."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log: dict[str, Any] = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Optional context fields
        request_id = getattr(record, "request_id", None)
        path = getattr(record, "path", None)
        if request_id:
            log["request_id"] = request_id
        if path:
            log["path"] = path
        return json.dumps(log, ensure_ascii=False)


def configure_logging() -> logging.Logger:
    """
    Configure root logger with JSON formatter and return the app logger.
    Safe to call multiple times (handlers will be reset).
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    return logging.getLogger("gert_backend")

{
  "cells": [],
  "metadata": {
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 2
}