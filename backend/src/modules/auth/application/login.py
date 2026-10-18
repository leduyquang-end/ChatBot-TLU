from __future__ import annotations

from dataclasses import dataclass

from src.modules.auth.application.ports.credential_checker import CredentialChecker
from src.modules.auth.application.ports.refresh_token_store import RefreshTokenStore
from src.modules.auth.application.ports.token_issuer import TokenIssuerPort
from src.shared.common.errors import UnauthorizedError


@dataclass(frozen=True)
class LoginResult:
    """Kiểu trả về của login — đóng gói kết quả, bất biến (frozen)."""

    token: str
    refresh_token: str
    user_id: str
    role: str


class LoginUseCase:
    """Nghiệp vụ đăng nhập.

    - Không biết HTTP (không import Flask, không đọc request).
    - Không biết hạ tầng (không import platform, infrastructure).
    - Phụ thuộc CredentialChecker + TokenIssuerPort + RefreshTokenStore — truyền qua constructor.
    - Lỗi nghiệp vụ → ném exception từ shared/common/errors.
    """

    _FAIL_MESSAGE = "Sai tài khoản hoặc mật khẩu"

    def __init__(
        self,
        checker: CredentialChecker,
        token_issuer: TokenIssuerPort,
        store: RefreshTokenStore,
    ) -> None:
        self._checker = checker
        self._token_issuer = token_issuer
        self._store = store

    def execute(self, username: str, password: str) -> LoginResult:
        # Kiểm tra nghiệp vụ phòng hờ (route đã kiểm tra thô rồi)
        if not username or not username.strip() or not password:
            raise UnauthorizedError(self._FAIL_MESSAGE)

        # Kiểm tra thông tin xác thực — sai ở bước nào cũng cùng một thông điệp
        if not self._checker.check(username.strip(), password):
            raise UnauthorizedError(self._FAIL_MESSAGE)

        user = self._checker.find_user(username.strip())
        if user is None:
            raise UnauthorizedError(self._FAIL_MESSAGE)

        token = self._token_issuer.issue(user.id)
        refresh = self._store.create(user.id)
        return LoginResult(
            token=token,
            refresh_token=refresh.token,
            user_id=user.id,
            role=user.role,
        )
