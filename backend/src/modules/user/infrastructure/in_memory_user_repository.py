from __future__ import annotations

import threading

from src.modules.user.domain.user import User
from src.platform.security.auth import hash_password, verify_password
from src.shared.common.errors import NotFoundError


class InMemoryUserRepository:
    """Repository tạm cho môi trường phát triển. Thay bằng DB thật sau."""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._credentials: dict[str, str] = {}

    def find_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def find_by_username(self, username: str) -> User | None:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def save(self, user: User) -> User:
        self._users[user.id] = user
        return user

    def list_all(self) -> list[User]:
        return list(self._users.values())

    def set_password(self, username: str, password: str) -> None:
        if self.find_by_username(username) is None:
            raise NotFoundError("Không tìm thấy người dùng")
        self._credentials[username] = hash_password(password)

    def check_password(self, username: str, password: str) -> bool:
        stored = self._credentials.get(username)
        if stored is None:
            return False
        return verify_password(password, stored)


_USER_REPOSITORY: InMemoryUserRepository | None = None
_USER_REPOSITORY_LOCK = threading.Lock()


def get_user_repository() -> InMemoryUserRepository:
    """Singleton an toàn luồng — seed xong mới gán (2 request cold start không seed đôi)."""
    global _USER_REPOSITORY
    if _USER_REPOSITORY is None:
        with _USER_REPOSITORY_LOCK:
            if _USER_REPOSITORY is None:
                repo = InMemoryUserRepository()
                _seed_demo_users(repo)
                _USER_REPOSITORY = repo
    return _USER_REPOSITORY


def reset_user_repository() -> None:
    """Xóa singleton để lần gọi sau seed lại — dùng cho test."""
    global _USER_REPOSITORY
    with _USER_REPOSITORY_LOCK:
        _USER_REPOSITORY = None


def _seed_demo_users(repo: InMemoryUserRepository) -> None:
    repo.save(User(id="u-001", username="sinhvien01", full_name="Sinh viên Demo", role="student"))
    repo.save(User(id="u-002", username="admin01", full_name="Quản trị viên", role="admin"))
    repo.set_password("sinhvien01", "demo-password")
    repo.set_password("admin01", "demo-password")
