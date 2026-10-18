from __future__ import annotations

from typing import Protocol


class TokenIssuerPort(Protocol):
    """Hợp đồng cấp token — application không biết cách ký/verify."""

    def issue(self, user_id: str) -> str: ...
