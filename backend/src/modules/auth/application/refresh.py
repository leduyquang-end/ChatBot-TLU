from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.auth.application.ports.refresh_token_store import RefreshTokenStore
from src.modules.auth.application.ports.token_issuer import TokenIssuerPort
from src.modules.auth.application.ports.user_lookup import UserLookup
from src.shared.common.errors import UnauthorizedError


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class RefreshResult:
    """Kiểu trả về của refresh — bất biến (frozen)."""

    token: str
    refresh_token: str
    user_id: str
    role: str


class RefreshTokenUseCase:
    """Nghiệp vụ dùng refresh token lấy access token mới mà không đăng nhập lại.

    - Không biết HTTP, không biết lưu phiên ở đâu — chỉ qua port RefreshTokenStore.
    - Xoay phiên (rotation): phiên cũ bị thu hồi ngay khi đổi — chuỗi lộ ra dùng lại không được.
    - Lỗi nghiệp vụ → ném UnauthorizedError (401) từ shared/common/errors.
    """

    _FAIL_MESSAGE = "Phiên đăng nhập đã hết hạn"

    def __init__(
        self,
        store: RefreshTokenStore,
        token_issuer: TokenIssuerPort,
        users: UserLookup,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._store = store
        self._token_issuer = token_issuer
        self._users = users
        self._clock = clock

    def execute(self, refresh_token: str) -> RefreshResult:
        # Kiểm tra nghiệp vụ phòng hờ (route đã kiểm tra thô rồi)
        if not refresh_token or not refresh_token.strip():
            raise UnauthorizedError(self._FAIL_MESSAGE)

        raw = refresh_token.strip()

        # Phiên không tồn tại (chưa từng có hoặc đã bị thu hồi)
        session = self._store.find(raw)
        if session is None:
            raise UnauthorizedError(self._FAIL_MESSAGE)

        # Phiên hết hạn → dọn luôn khỏi kho
        if session.is_expired(self._clock()):
            self._store.revoke(raw)
            raise UnauthorizedError(self._FAIL_MESSAGE)

        # User bị xóa thì phiên cũng không dùng được → thu hồi
        user = self._users.find_by_id(session.user_id)
        if user is None:
            self._store.revoke(raw)
            raise UnauthorizedError(self._FAIL_MESSAGE)

        # Xoay phiên: thu hồi phiên cũ, tạo phiên mới
        self._store.revoke(raw)
        new_session = self._store.create(user.id)
        token = self._token_issuer.issue(user.id)
        return RefreshResult(
            token=token,
            refresh_token=new_session.token,
            user_id=user.id,
            role=user.role,
        )
