from __future__ import annotations

from src.modules.user.application.ports.user_repository import UserRepository
from src.modules.user.domain.user import User
from src.shared.common.errors import NotFoundError


class UpdateMyProfile:
    """Cập nhật họ tên của chính user hiện tại (PUT /user/me).

    Quy tắc họ tên nằm ở domain (`User.with_full_name`).
    """

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def execute(self, user_id: str, full_name: str) -> User:
        user = self._repository.find_by_id(user_id)
        if user is None:
            raise NotFoundError("Không tìm thấy người dùng")
        updated = user.with_full_name(full_name)
        return self._repository.save(updated)
