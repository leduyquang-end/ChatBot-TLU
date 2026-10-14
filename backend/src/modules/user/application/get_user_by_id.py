from __future__ import annotations

from src.modules.user.application.ports.user_repository import UserRepository
from src.modules.user.domain.user import User
from src.shared.common.errors import NotFoundError


class GetUserById:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def execute(self, user_id: str) -> User:
        user = self._repository.find_by_id(user_id)
        if user is None:
            raise NotFoundError("Không tìm thấy người dùng")
        return user
