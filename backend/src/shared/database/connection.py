from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from src.shared.common.errors import ConfigError
from src.shared.config.settings import get_settings

_SQLITE_PREFIX = "sqlite:///"


def _parse(url: str) -> tuple[str, str]:
    """Tách (cơ_sở, mục_tiêu) khỏi DATABASE_URL. Sai định dạng → ConfigError."""
    if url.startswith(_SQLITE_PREFIX):
        target = url[len(_SQLITE_PREFIX) :]
        if not target:
            raise ConfigError("DATABASE_URL dạng sqlite thiếu đường dẫn file")
        return "sqlite", target
    if "://" in url:
        scheme = url.split("://", 1)[0].lower()
        return scheme, ""
    raise ConfigError(f"DATABASE_URL không hợp lệ: {url!r}")


def connect(url: str) -> sqlite3.Connection:
    """Mở connection theo URL.

    Hiện hỗ trợ `sqlite:///<file>` (stdlib — không cần cài thêm gì).
    MySQL/PostgreSQL... chưa hỗ trợ → ConfigError rõ ràng.
    """
    scheme, target = _parse(url)
    if scheme != "sqlite":
        raise ConfigError(
            f"Chưa hỗ trợ cơ sở dữ liệu {scheme!r} — hiện chỉ có sqlite"
        )
    path = Path(target)
    if str(path.parent) not in ("", "."):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_connection() -> sqlite3.Connection:
    """Mở connection theo `Settings.database_url`.

    Mỗi lần gọi một connection mới — sqlite3 connection không thread-safe.
    """
    return connect(get_settings().database_url)


@contextmanager
def db_connection() -> Iterator[sqlite3.Connection]:
    """Dùng trong `with` — tự đóng connection khi ra ngoài."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
