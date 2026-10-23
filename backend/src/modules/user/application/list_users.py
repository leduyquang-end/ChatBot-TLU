from __future__ import annotations

from src.modules.user.application.ports.user_repository import UserRepository
from src.modules.user.domain.user import User


class ListUsers:
    """Liệt kê toàn bộ user (GET /user — chỉ admin).

    Kiểm tra quyền do api layer thực hiện (AGENT.md 11.2: mỗi route có kiểm tra quyền ở `api`).
    """

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def execute(self) -> list[User]:
        return sorted(self._repository.list_all(), key=lambda user: user.id)
