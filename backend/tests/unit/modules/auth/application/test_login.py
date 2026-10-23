from datetime import UTC, datetime, timedelta

import pytest

from src.modules.auth.application.login import LoginResult, LoginUseCase
from src.modules.auth.domain.refresh_token import RefreshToken
from src.modules.user.domain.user import User
from src.shared.common.errors import UnauthorizedError
from src.shared.events import EventBus, UserLoggedIn

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class FakeChecker:
    """Fake CredentialChecker — không cần DB thật."""

    def __init__(self, *, valid: bool = True, user: User | None = None) -> None:
        self._valid = valid
        self._user = user

    def check(self, username: str, password: str) -> User | None:
        return self._user if self._valid else None


class FakeTokenIssuer:
    """Fake TokenIssuerPort — trả token dựng sẵn, không ký thật."""

    def __init__(self) -> None:
        self.issued_for: list[str] = []

    def issue(self, user_id: str) -> str:
        self.issued_for.append(user_id)
        return f"fake-token-{user_id}"


class FakeStore:
    """Fake RefreshTokenStore — tạo phiên trong RAM, ghi lại lần gọi."""

    def __init__(self) -> None:
        self.sessions: dict[str, RefreshToken] = {}
        self.created_for: list[str] = []
        self._seq = 0

    def create(self, user_id: str) -> RefreshToken:
        self._seq += 1
        session = RefreshToken(
            token=f"rt-{self._seq}",
            user_id=user_id,
            issued_at=NOW,
            expires_at=NOW + timedelta(days=30),
        )
        self.sessions[session.token] = session
        self.created_for.append(user_id)
        return session

    def find(self, raw_token: str) -> RefreshToken | None:
        return self.sessions.get(raw_token)

    def revoke(self, raw_token: str) -> None:
        self.sessions.pop(raw_token, None)


DEMO_USER = User(id="u-001", username="sinhvien01", full_name="SV Demo", role="student")


def make_use_case(
    *, valid: bool = True, user: User | None = DEMO_USER
) -> tuple[LoginUseCase, FakeTokenIssuer, FakeStore]:
    issuer = FakeTokenIssuer()
    store = FakeStore()
    use_case = LoginUseCase(
        checker=FakeChecker(valid=valid, user=user),
        token_issuer=issuer,
        store=store,
        event_bus=EventBus(),
    )
    return use_case, issuer, store


def test_login_thanh_cong_tra_ve_login_result():
    use_case, issuer, _store = make_use_case()
    result = use_case.execute("sinhvien01", "demo-password")
    assert isinstance(result, LoginResult)
    assert result.user_id == "u-001"
    assert result.role == "student"
    assert result.token == "fake-token-u-001"
    assert issuer.issued_for == ["u-001"]


def test_login_tao_phien_refresh():
    use_case, _, store = make_use_case()
    result = use_case.execute("sinhvien01", "demo-password")
    assert result.refresh_token == "rt-1"
    assert store.created_for == ["u-001"]
    assert store.find(result.refresh_token) is not None


def test_sai_mat_khau_nem_unauthorized():
    use_case, _, _ = make_use_case(valid=False, user=None)
    with pytest.raises(UnauthorizedError) as exc:
        use_case.execute("sinhvien01", "sai")
    assert exc.value.code == "UNAUTHORIZED"
    assert exc.value.http_status == 401


def test_user_khong_ton_tai_nem_unauthorized():
    use_case, _, _ = make_use_case(valid=True, user=None)
    with pytest.raises(UnauthorizedError):
        use_case.execute("khong-ton-tai", "password")


def test_username_rong_nem_unauthorized():
    use_case, _, _ = make_use_case()
    with pytest.raises(UnauthorizedError):
        use_case.execute("", "password")
    with pytest.raises(UnauthorizedError):
        use_case.execute("   ", "password")


def test_password_rong_nem_unauthorized():
    use_case, _, _ = make_use_case()
    with pytest.raises(UnauthorizedError):
        use_case.execute("sinhvien01", "")


def test_khong_tiet_lo_buoc_sai_tai_thong_diep():
    """Mọi fail đều cùng một thông điệp — không lộ sai ở bước nào."""
    msg = "Sai tài khoản hoặc mật khẩu"
    uc1, _, _ = make_use_case(valid=False, user=None)
    uc2, _, _ = make_use_case(valid=True, user=None)
    with pytest.raises(UnauthorizedError) as e1:
        uc1.execute("u", "p")
    with pytest.raises(UnauthorizedError) as e2:
        uc2.execute("u", "p")
    assert e1.value.message == msg
    assert e2.value.message == msg


def test_login_thanh_cong_phat_su_kien_user_logged_in():
    bus = EventBus()
    received: list[UserLoggedIn] = []
    bus.subscribe(UserLoggedIn, received.append)

    LoginUseCase(
        checker=FakeChecker(user=DEMO_USER),
        token_issuer=FakeTokenIssuer(),
        store=FakeStore(),
        event_bus=bus,
    ).execute("sinhvien01", "demo-password")

    assert received == [UserLoggedIn(user_id="u-001", role="student")]


def test_login_that_bai_khong_phat_su_kien():
    bus = EventBus()
    received: list[UserLoggedIn] = []
    bus.subscribe(UserLoggedIn, received.append)

    with pytest.raises(UnauthorizedError):
        LoginUseCase(
            checker=FakeChecker(valid=False, user=None),
            token_issuer=FakeTokenIssuer(),
            store=FakeStore(),
            event_bus=bus,
        ).execute("sinhvien01", "sai")

    assert received == []
