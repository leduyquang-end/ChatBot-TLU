from __future__ import annotations

from typing import Protocol

from src.modules.auth.application.ports.user_lookup import UserRecord


class CredentialRepository(Protocol):
    def find_by_username(self, username: str) -> UserRecord | None: ...

    def check_password(self, username: str, password: str) -> bool: ...


class CredentialChecker(Protocol):
    def check(self, username: str, password: str) -> UserRecord | None: ...
