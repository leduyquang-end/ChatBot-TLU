from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import time

from src.shared.common.errors import ForbiddenError, UnauthorizedError

logger = logging.getLogger(__name__)

# Giữ an toàn với dò CPU qua PBKDF2: mật khẩu dài bất thường bị cắt ở mức này
# (cả khi hash lẫn khi verify — nhất quán, như bcrypt cắt ở 72 byte)
_MAX_PASSWORD_CHARS = 1024

_DEFAULT_SECRET = "dev-only-secret-change-me"
_MIN_SECRET_LENGTH = 16
_secret_warnings: set[str] = set()


def _warn_once(key: str, message: str) -> None:
    if key in _secret_warnings:
        return
    _secret_warnings.add(key)
    logger.warning(message)


def _get_secret() -> str:
    """Đọc APP_SECRET từ môi trường (AGENT.md 11.1). Thiếu → secret dev; ngắn → cảnh báo."""
    secret = os.environ.get("APP_SECRET", "").strip()
    if not secret:
        _warn_once("default_secret", "event=security.default_secret source=env fallback=dev")
        return _DEFAULT_SECRET
    if len(secret) < _MIN_SECRET_LENGTH:
        _warn_once(
            "weak_secret", f"event=security.weak_secret length={len(secret)}"
        )
    return secret


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    if salt is None:
        salt = secrets.token_bytes(16)
    material = password[:_MAX_PASSWORD_CHARS].encode("utf-8")
    digest = hashlib.pbkdf2_hmac("sha256", material, salt, 200_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    material = password[:_MAX_PASSWORD_CHARS].encode("utf-8")
    candidate = hashlib.pbkdf2_hmac("sha256", material, salt, 200_000)
    return hmac.compare_digest(candidate, expected)


def issue_token(user_id: str, *, ttl_seconds: int = 86400) -> str:
    # time.time() là đồng hồ tường (epoch) — nhất quán giữa mọi worker/process/máy.
    # (os.times().elapsed = 0.0 cố định trên Windows → token không bao giờ hết hạn.)
    expires = int(time.time()) + ttl_seconds
    payload = f"{user_id}.{expires}"
    secret = _get_secret()
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def verify_token(token: str) -> str:
    """Trả về user_id. Ném UnauthorizedError nếu không hợp lệ/hết hạn."""
    try:
        user_id, expires, signature = token.rsplit(".", 2)
        payload = f"{user_id}.{expires}"
    except ValueError as exc:
        raise UnauthorizedError("Token không hợp lệ") from exc
    secret = _get_secret()
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    # So sánh dạng bytes — compare_digest ném TypeError với chuỗi không phải ASCII
    if not hmac.compare_digest(signature.encode("utf-8"), expected.encode("utf-8")):
        raise UnauthorizedError("Token không hợp lệ")
    try:
        if int(expires) < int(time.time()):
            raise UnauthorizedError("Token đã hết hạn")
    except ValueError as exc:
        raise UnauthorizedError("Token không hợp lệ") from exc
    return user_id


def require_role(user_role: str, allowed: set[str]) -> None:
    if user_role not in allowed:
        raise ForbiddenError("Bạn không có quyền thực hiện thao tác này")


def sanitize_input(text: str, *, max_length: int) -> str:
    """Lọc ký tự điều khiển, cắt theo độ dài tối đa (bỏ khoảng trắng sót lại sau khi cắt)."""
    cleaned = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ch.isprintable())
    return cleaned.strip()[:max_length].rstrip()
