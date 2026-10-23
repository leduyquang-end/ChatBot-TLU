from __future__ import annotations

from dataclasses import dataclass, replace

from src.shared.common.errors import ValidationError

ROLE_STUDENT = "student"
ROLE_ADMIN = "admin"

FULL_NAME_MAX_LENGTH = 100

_VALID_ROLES = {ROLE_STUDENT, ROLE_ADMIN}


def _check_full_name(value: str) -> None:
    """Quy tắc họ tên — thuần domain, sai → ValueError (lệch khi tạo entity)."""
    if not value or not value.strip():
        raise ValueError("Họ và tên không được rỗng")
    if len(value) > FULL_NAME_MAX_LENGTH:
        raise ValueError(f"Họ và tên tối đa {FULL_NAME_MAX_LENGTH} ký tự")


@dataclass(frozen=True)
class User:
    id: str
    username: str
    full_name: str
    role: str

    def __post_init__(self) -> None:
        if self.role not in _VALID_ROLES:
            raise ValueError(f"Vai trò không hợp lệ: {self.role}")
        _check_full_name(self.full_name)

    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    def with_full_name(self, full_name: str) -> User:
        """Trả về bản sao với họ tên mới (bất biến) — input sai → ValidationError (400)."""
        cleaned = full_name.strip()
        try:
            _check_full_name(cleaned)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return replace(self, full_name=cleaned)
