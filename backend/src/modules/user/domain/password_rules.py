from __future__ import annotations

from src.shared.common.errors import ValidationError

PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 128


def validate_password_format(password: str) -> None:
    """Định dạng mật khẩu mới — sai độ dài → ValidationError (400)."""
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise ValidationError(
            f"Mật khẩu mới phải từ {PASSWORD_MIN_LENGTH} đến {PASSWORD_MAX_LENGTH} ký tự"
        )


def ensure_password_changed(old_password: str, new_password: str) -> None:
    """Mật khẩu mới phải khác mật khẩu cũ — trùng → ValidationError (400)."""
    if new_password == old_password:
        raise ValidationError("Mật khẩu mới phải khác mật khẩu cũ")
