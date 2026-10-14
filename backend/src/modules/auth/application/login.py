from __future__ import annotations

from dataclasses import dataclass

from src.modules.auth.application.ports.credential_checker import CredentialChecker
from src.shared.common.errors import UnauthorizedError
from src.platform.security.auth import issue_token


@dataclass(frozen=True)
class LoginResult:
    token: str
    user_id: str
    role: str


class LoginUseCase:
    def __init__(self, checker: CredentialChecker) -> None:
        self._checker = checker

    def execute(self, username: str, password: str) -> LoginResult:
        if not username or not password:
            raise UnauthorizedError("Sai tài khoản hoặc mật khẩu")
        if not self._checker.check(username, password):
            raise UnauthorizedError("Sai tài khoản hoặc mật khẩu")
        user = self._checker.find_user(username)
        if user is None:
            raise UnauthorizedError("Sai tài khoản hoặc mật khẩu")
        token = issue_token(user.id)
        return LoginResult(token=token, user_id=user.id, role=user.role)
