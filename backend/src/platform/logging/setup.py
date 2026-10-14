from __future__ import annotations

import logging
import sys
from typing import Any

_CONFIGURED = False

# Khóa tuyệt đối không được ghi vào log ở mức INFO trở lên
_FORBIDDEN_KEYS = {
    "password",
    "api_key",
    "apikey",
    "token",
    "secret",
    "authorization",
    "question",
    "answer",
    "content",
    "chunk_text",
    "mssv",
    "email",
    "phone",
}


def _redact(data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    safe: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in _FORBIDDEN_KEYS:
            safe[key] = "[REDACTED]"
        else:
            safe[key] = value
    return safe


class EventLogRecord(logging.LogRecord):
    extra_fields: dict[str, Any]


def setup_logging(level: str = "INFO") -> None:
    """Cấu hình log: mỗi dòng một sự kiện, có mức, thời gian, thông tin kèm."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s level=%(levelname)s %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    **fields: Any,
) -> None:
    """Ghi một sự kiện. Tự redact các khóa nhạy cảm."""
    safe = _redact(fields)
    parts = [f"event={event}"]
    for key, value in safe.items():
        parts.append(f"{key}={value}")
    logger.log(level, " ".join(parts))
