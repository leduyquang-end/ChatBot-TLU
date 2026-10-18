from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from collections.abc import Callable

from src.shared.common.errors import ForbiddenError, UnauthorizedError


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return hmac.compare_digest(candidate, expected)


def issue_token(user_id: str, *, ttl_seconds: int = 86400) -> str:
    expires = int(os.times().elapsed) + ttl_seconds
    payload = f"{user_id}.{expires}"
    secret = os.environ.get("APP_SECRET", "dev-only-secret-change-me")
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def verify_token(token: str) -> str:
    """Trả về user_id. Ném UnauthorizedError nếu không hợp lệ."""
    try:
        user_id, expires, signature = token.rsplit(".", 2)
        payload = f"{user_id}.{expires}"
    except ValueError as exc:
        raise UnauthorizedError("Token không hợp lệ") from exc
    secret = os.environ.get("APP_SECRET", "dev-only-secret-change-me")
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise UnauthorizedError("Token không hợp lệ")
    try:
        if int(expires) < int(os.times().elapsed):
            raise UnauthorizedError("Token đã hết hạn")
    except ValueError as exc:
        raise UnauthorizedError("Token không hợp lệ") from exc
    return user_id


def require_role(user_role: str, allowed: set[str]) -> None:
    if user_role not in allowed:
        raise ForbiddenError("Bạn không có quyền thực hiện thao tác này")


def sanitize_input(text: str, *, max_length: int) -> str:
    """Lọc ký tự điều khiển, cắt theo độ dài tối đa."""
    cleaned = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ch.isprintable())
    cleaned = cleaned.strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


RequestGuard = Callable[..., None]
