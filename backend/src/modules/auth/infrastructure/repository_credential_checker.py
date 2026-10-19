from __future__ import annotations

from src.modules.user.domain.user import User
from src.modules.user.infrastructure.in_memory_user_repository import (
    InMemoryUserRepository,
    get_user_repository,
)


class RepositoryCredentialChecker:
    def __init__(self, repository: InMemoryUserRepository | None = None) -> None:
        self._repository = repository or get_user_repository()

    def check(self, username: str, password: str) -> bool:
        return self._repository.check_password(username, password)

    def find_user(self, username: str) -> User | None:
        return self._repository.find_by_username(username)
