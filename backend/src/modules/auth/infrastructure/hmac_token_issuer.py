from __future__ import annotations

from src.platform.security.auth import issue_token


class HmacTokenIssuer:
    """Cài TokenIssuerPort bằng HMAC token có sẵn trong platform/security."""

    def issue(self, user_id: str) -> str:
        return issue_token(user_id)
