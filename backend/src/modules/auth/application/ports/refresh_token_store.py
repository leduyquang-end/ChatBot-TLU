from __future__ import annotations

from typing import Protocol

from src.modules.auth.domain.refresh_token import RefreshToken


class RefreshTokenStore(Protocol):
    """Hợp đồng lưu phiên refresh — application không biết lưu ở đâu (RAM, Redis, DB…)."""

    def create(self, user_id: str) -> RefreshToken:
        """Tạo phiên mới cho user (application không tự sinh chuỗi bí mật)."""
        ...

    def find(self, raw_token: str) -> RefreshToken | None:
        """Tra phiên theo chuỗi gốc. None nếu không tồn tại (đã thu hồi hoặc chưa từng có)."""
        ...

    def revoke(self, raw_token: str) -> None:
        """Thu hồi phiên. Gọi với chuỗi không tồn tại thì vẫn vô hại (idempotent)."""
        ...
