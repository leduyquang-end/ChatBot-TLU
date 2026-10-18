from datetime import UTC, datetime, timedelta

import pytest

from src.modules.auth.application.refresh import RefreshResult, RefreshTokenUseCase
from src.modules.auth.domain.refresh_token import RefreshToken
from src.modules.user.domain.user import User
from src.shared.common.errors import UnauthorizedError

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
TTL = timedelta(days=30)

DEMO_USER = User(id="u-001", username="sinhvien01", full_name="SV Demo", role="student")


class FakeStore:
    """Fake RefreshTokenStore — chứa sẵn phiên, ghi lại lần thu hồi."""

    def __init__(self) -> None:
        self.sessions: dict[str, RefreshToken] = {}
        self.revoked: list[str] = []
        self._seq = 0

    def create(self, user_id: str) -> RefreshToken:
        self._seq += 1
        session = RefreshToken(
            token=f"rt-{self._seq}",
            user_id=user_id,
            issued_at=NOW,
            expires_at=NOW + TTL,
        )
        self.sessions[session.token] = session
        return session

    def seed(self, session: RefreshToken) -> None:
        """Đưa sẵn một phiên vào kho (dùng cho ca hết hạn / user đã xóa)."""
        self.sessions[session.token] = session

    def find(self, raw_token: str) -> RefreshToken | None:
        return self.sessions.get(raw_token)

    def revoke(self, raw_token: str) -> None:
        self.revoked.append(raw_token)
        self.sessions.pop(raw_token, None)


class FakeTokenIssuer:
    def issue(self, user_id: str) -> str:
        return f"fake-token-{user_id}"


class FakeUsers:
    """Fake UserRepository — test chỉ cần find_by_id."""

    def __init__(self, users: tuple[User, ...] = (DEMO_USER,)) -> None:
        self._users = {u.id: u for u in users}

    def find_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)


def make_use_case(
    *, users: tuple[User, ...] = (DEMO_USER,)
) -> tuple[RefreshTokenUseCase, FakeStore]:
    store = FakeStore()
    use_case = RefreshTokenUseCase(
        store=store,
        token_issuer=FakeTokenIssuer(),
        users=FakeUsers(users),
        clock=lambda: NOW,
    )
    return use_case, store


def test_refresh_thanh_cong_xoay_phien():
    use_case, store = make_use_case()
    old = store.create("u-001")

    result = use_case.execute(old.token)

    assert isinstance(result, RefreshResult)
    assert result.token == "fake-token-u-001"
    assert result.user_id == "u-001"
    assert result.role == "student"
    # Xoay phiên: phiên mới khác phiên cũ, phiên cũ bị thu hồi
    assert result.refresh_token != old.token
    assert old.token in store.revoked
    assert store.find(old.token) is None
    assert store.find(result.refresh_token) is not None


def test_refresh_phien_khong_ton_tai_nem_unauthorized():
    use_case, store = make_use_case()
    with pytest.raises(UnauthorizedError) as exc:
        use_case.execute("khong-ton-tai")
    assert exc.value.http_status == 401
    assert store.revoked == []


def test_refresh_phien_het_han_thu_hoi_va_nem_unauthorized():
    use_case, store = make_use_case()
    expired = RefreshToken(
        token="rt-het-han",
        user_id="u-001",
        issued_at=NOW - TTL - timedelta(hours=1),
        expires_at=NOW - timedelta(hours=1),
    )
    store.seed(expired)

    with pytest.raises(UnauthorizedError) as exc:
        use_case.execute("rt-het-han")

    assert exc.value.http_status == 401
    # Phiên hết hạn bị dọn khỏi kho
    assert store.find("rt-het-han") is None


def test_refresh_user_bi_xoa_thu_hoi_va_nem_unauthorized():
    use_case, store = make_use_case(users=())
    old = store.create("u-001")

    with pytest.raises(UnauthorizedError):
        use_case.execute(old.token)

    assert store.find(old.token) is None


def test_refresh_chuoi_rong_nem_unauthorized():
    use_case, _ = make_use_case()
    with pytest.raises(UnauthorizedError):
        use_case.execute("")
    with pytest.raises(UnauthorizedError):
        use_case.execute("   ")


def test_khong_tiet_lo_ly_do_tai_thong_diep():
    """Không rõ ràng: hết hạn / không tồn tại / user xóa — đều cùng một thông điệp."""
    msg = "Phiên đăng nhập đã hết hạn"
    uc1, _ = make_use_case()
    uc2, store2 = make_use_case()
    uc3, store3 = make_use_case(users=())

    with pytest.raises(UnauthorizedError) as e1:
        uc1.execute("khong-ton-tai")

    expired = RefreshToken(
        token="rt-cu",
        user_id="u-001",
        issued_at=NOW - TTL - timedelta(hours=1),
        expires_at=NOW - timedelta(hours=1),
    )
    store2.seed(expired)
    with pytest.raises(UnauthorizedError) as e2:
        uc2.execute("rt-cu")

    old = store3.create("u-001")
    with pytest.raises(UnauthorizedError) as e3:
        uc3.execute(old.token)

    assert e1.value.message == msg
    assert e2.value.message == msg
    assert e3.value.message == msg
