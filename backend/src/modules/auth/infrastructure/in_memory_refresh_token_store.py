from __future__ import annotations

import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from src.modules.auth.domain.refresh_token import RefreshToken
from src.shared.config.settings import get_settings


def _utc_now() -> datetime:
    return datetime.now(UTC)


class InMemoryRefreshTokenStore:
    """Lưu phiên refresh trong RAM — tạm cho dev, thay Redis/DB khi chạy nhiều worker.

    - Sinh chuỗi bí mật (secrets) và tính hạn ở đây — application không biết cách sinh.
    - now_fn cho phép test ghim thời gian (không cần chờ hết hạn thật).
    """

    def __init__(
        self,
        *,
        ttl_seconds: int,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._now = now_fn
        self._sessions: dict[str, RefreshToken] = {}

    def create(self, user_id: str) -> RefreshToken:
        now = self._now()
        session = RefreshToken(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            issued_at=now,
            expires_at=now + self._ttl,
        )
        self._sessions[session.token] = session
        return session

    def find(self, raw_token: str) -> RefreshToken | None:
        return self._sessions.get(raw_token)

    def revoke(self, raw_token: str) -> None:
        self._sessions.pop(raw_token, None)


_STORE: InMemoryRefreshTokenStore | None = None


def get_refresh_token_store() -> InMemoryRefreshTokenStore:
    """Singleton — phiên phải sống qua nhiều request, không tạo lại mỗi lần gọi."""
    global _STORE
    if _STORE is None:
        _STORE = InMemoryRefreshTokenStore(
            ttl_seconds=get_settings().refresh_token_ttl_hours * 3600,
        )
    return _STORE
