from __future__ import annotations

from dataclasses import dataclass

from src.modules.auth.application.ports.refresh_token_store import RefreshTokenStore


@dataclass(frozen=True)
class LogoutResult:
    """Kiểu trả về của logout — revoked=True nếu thực sự thu hồi được phiên."""

    revoked: bool


class LogoutUseCase:
    """Nghiệp vụ đăng xuất — thu hồi refresh token để không lấy được token mới nữa.

    - Idempotent: chuỗi không tồn tại / đã thu hồi rồi → vẫn trả về thành công (revoked=False).
      Đăng xuất là hành động an toàn, gọi lại bao nhiêu lần cũng không được báo lỗi.
    - Không biết HTTP, không biết lưu phiên ở đâu — chỉ qua port RefreshTokenStore.
    - Lưu ý: access token cũ vẫn sống tới khi hết hạn (xem README auth/infrastructure/).
    """

    def __init__(self, store: RefreshTokenStore) -> None:
        self._store = store

    def execute(self, refresh_token: str) -> LogoutResult:
        if not refresh_token or not refresh_token.strip():
            return LogoutResult(revoked=False)

        raw = refresh_token.strip()
        if self._store.find(raw) is None:
            return LogoutResult(revoked=False)

        self._store.revoke(raw)
        return LogoutResult(revoked=True)
