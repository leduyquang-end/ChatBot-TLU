from __future__ import annotations

from src.modules.user.application.ports.user_repository import UserRepository
from src.modules.user.domain.password_rules import (
    ensure_password_changed,
    validate_password_format,
)
from src.shared.common.errors import NotFoundError, UnauthorizedError
from src.shared.events import EventBus, UserPasswordChanged


class ChangePassword:
    """Đổi mật khẩu của chính user hiện tại (POST /user/change-password).

    - Mật khẩu mới sai định dạng hoặc trùng cũ → ValidationError (400) — quy tắc ở domain.
    - Mật khẩu cũ sai → UnauthorizedError (401) — cùng nhóm lỗi với đăng nhập sai.
    """

    def __init__(self, repository: UserRepository, event_bus: EventBus) -> None:
        self._repository = repository
        self._event_bus = event_bus

    def execute(self, user_id: str, old_password: str, new_password: str) -> None:
        user = self._repository.find_by_id(user_id)
        if user is None:
            raise NotFoundError("Không tìm thấy người dùng")

        validate_password_format(new_password)

        if not self._repository.check_password(user.username, old_password):
            raise UnauthorizedError("Mật khẩu cũ không đúng")

        ensure_password_changed(old_password, new_password)

        self._repository.set_password(user.username, new_password)
        self._event_bus.publish(UserPasswordChanged(user_id=user.id))
