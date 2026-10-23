from __future__ import annotations

from src.modules.auth.application.ports.credential_checker import CredentialRepository
from src.modules.auth.application.ports.user_lookup import UserRecord


class RepositoryCredentialChecker:
    """Cài CredentialChecker qua repository truyền vào — không biết module user."""

    def __init__(self, repository: CredentialRepository) -> None:
        self._repository = repository

    def check(self, username: str, password: str) -> UserRecord | None:
        user = self._repository.find_by_username(username)
        if user is None or not self._repository.check_password(username, password):
            return None
        return user
