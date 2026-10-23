from __future__ import annotations

from src.modules.user.domain.user import User

DEMO_USER = User(
    id="u-001", username="sinhvien01", full_name="Sinh viên Demo", role="student"
)
ADMIN_USER = User(
    id="u-002", username="admin01", full_name="Quản trị viên", role="admin"
)


class FakeUserRepository:
    """Fake UserRepository — đủ cho test application, không cần hashing thật."""

    def __init__(self, users: list[User] | None = None) -> None:
        self._users: dict[str, User] = {user.id: user for user in (users or [])}
        self.passwords: dict[str, str] = {}
        self.saved: list[User] = []
        self.set_password_calls: list[tuple[str, str]] = []

    def find_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def find_by_username(self, username: str) -> User | None:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def save(self, user: User) -> User:
        self._users[user.id] = user
        self.saved.append(user)
        return user

    def list_all(self) -> list[User]:
        return list(self._users.values())

    def set_password(self, username: str, password: str) -> None:
        self.passwords[username] = password
        self.set_password_calls.append((username, password))

    def check_password(self, username: str, password: str) -> bool:
        return self.passwords.get(username) == password
