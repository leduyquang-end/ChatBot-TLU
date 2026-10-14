from __future__ import annotations

from typing import Protocol

from src.modules.user.domain.user import User


class CredentialChecker(Protocol):
    def check(self, username: str, password: str) -> bool: ...

    def find_user(self, username: str) -> User | None: ...
