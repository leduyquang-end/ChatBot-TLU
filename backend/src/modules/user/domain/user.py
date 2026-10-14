from __future__ import annotations

from dataclasses import dataclass

ROLE_STUDENT = "student"
ROLE_ADMIN = "admin"

_VALID_ROLES = {ROLE_STUDENT, ROLE_ADMIN}


@dataclass(frozen=True)
class User:
    id: str
    username: str
    full_name: str
    role: str

    def __post_init__(self) -> None:
        if self.role not in _VALID_ROLES:
            raise ValueError(f"Vai trò không hợp lệ: {self.role}")

    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN
