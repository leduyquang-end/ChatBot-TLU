from __future__ import annotations

import logging
import sys
import threading
from typing import Any

_CONFIGURED = False
_SETUP_LOCK = threading.Lock()

# Đoạn khóa nằm trong đây → giá trị bị che khi ghi log (AGENT.md 10.2, 11.1):
# câu hỏi/trả lời/nội dung đoạn, khóa API, mật khẩu, token, thông tin cá nhân.
_FORBIDDEN_KEY_FRAGMENTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "private_key",
    "question",
    "answer",
    "content",
    "chunk_text",
    "mssv",
    "email",
    "phone",
    "sdt",
    "full_name",
    "hoten",
)
_REDACTED = "[REDACTED]"


def _is_forbidden_key(key: Any) -> bool:
    """So khớp theo đoạn khóa (không phân biệt hoa thường) — user_password, access_token... đều bị bắt."""
    lowered = str(key).lower()
    return any(fragment in lowered for fragment in _FORBIDDEN_KEY_FRAGMENTS)


def _redact(value: Any) -> Any:
    """Che giá trị nhạy cảm — đệ quy vào dict/list lồng nhau."""
    if isinstance(value, dict):
        return {
            key: _REDACTED if _is_forbidden_key(key) else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


def _format_key(key: Any) -> str:
    text = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(key))
    return text or "field"


def _format_value(value: Any) -> str:
    """Giá trị không được làm vỡ quy tắc 'mỗi dòng một sự kiện' (AGENT.md 10.3)."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).replace("\r", "\\r").replace("\n", "\\n")
    if not text:
        return '""'
    if any(ch.isspace() for ch in text) or '"' in text:
        return '"' + text.replace('"', "'") + '"'
    return text


def _resolve_level(level: str | int) -> int:
    """Đọc mức log; mức không tồn tại → INFO (cảnh báo event=logging.bad_level)."""
    if isinstance(level, int):
        return level
    name = str(level).strip().upper()
    resolved = logging.getLevelNamesMapping().get(name)
    if isinstance(resolved, int):
        return resolved
    logging.getLogger(__name__).warning(
        "event=logging.bad_level level=%s fallback=INFO", level
    )
    return logging.INFO


def setup_logging(level: str = "INFO", *, force: bool = False) -> None:
    """Cấu hình log: mỗi dòng một sự kiện, có mức, thời gian, thông tin kèm.

    Gọi một lần khi khởi động (AGENT.md 10.3); force=True để cấu hình lại (test/script).
    """
    global _CONFIGURED
    with _SETUP_LOCK:
        if _CONFIGURED and not force:
            return
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s level=%(levelname)s %(message)s")
        )
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(_resolve_level(level))
        _CONFIGURED = True


def reset_logging() -> None:
    """Gỡ cấu hình log — chỉ dùng cho test hoặc khi cần cấu hình lại từ đầu."""
    global _CONFIGURED
    with _SETUP_LOCK:
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)
        _CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    level: int | str,
    event: str,
    **fields: Any,
) -> None:
    """Ghi một sự kiện dạng `event=... key=value` — tự redact khóa nhạy cảm (kể cả lồng nhau)."""
    safe = _redact(fields)
    parts = [f"event={_format_key(event)}"]
    for key, value in safe.items():
        parts.append(f"{_format_key(key)}={_format_value(value)}")
    logger.log(_resolve_level(level), " ".join(parts))
