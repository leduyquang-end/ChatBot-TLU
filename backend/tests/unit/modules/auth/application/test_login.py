import pytest

from src.modules.auth.application.login import LoginResult, LoginUseCase
from src.modules.user.domain.user import User
from src.shared.common.errors import UnauthorizedError


class FakeChecker:
    """Fake CredentialChecker — không cần DB thật."""

    def __init__(self, *, valid: bool = True, user: User | None = None) -> None:
        self._valid = valid
        self._user = user

    def check(self, username: str, password: str) -> bool:
        return self._valid

    def find_user(self, username: str) -> User | None:
        return self._user


class FakeTokenIssuer:
    """Fake TokenIssuerPort — trả token dựng sẵn, không ký thật."""

    def __init__(self) -> None:
        self.issued_for: list[str] = []

    def issue(self, user_id: str) -> str:
        self.issued_for.append(user_id)
        return f"fake-token-{user_id}"


DEMO_USER = User(id="u-001", username="sinhvien01", full_name="SV Demo", role="student")


def make_use_case(*, valid: bool = True, user: User | None = DEMO_USER) -> tuple[LoginUseCase, FakeTokenIssuer]:
    issuer = FakeTokenIssuer()
    use_case = LoginUseCase(checker=FakeChecker(valid=valid, user=user), token_issuer=issuer)
    return use_case, issuer


def test_login_thanh_cong_tra_ve_login_result():
    use_case, issuer = make_use_case()
    result = use_case.execute("sinhvien01", "demo-password")
    assert isinstance(result, LoginResult)
    assert result.user_id == "u-001"
    assert result.role == "student"
    assert result.token == "fake-token-u-001"
    assert issuer.issued_for == ["u-001"]


def test_sai_mat_khau_nem_unauthorized():
    use_case, _ = make_use_case(valid=False, user=None)
    with pytest.raises(UnauthorizedError) as exc:
        use_case.execute("sinhvien01", "sai")
    assert exc.value.code == "UNAUTHORIZED"
    assert exc.value.http_status == 401


def test_user_khong_ton_tai_nem_unauthorized():
    use_case, _ = make_use_case(valid=True, user=None)
    with pytest.raises(UnauthorizedError):
        use_case.execute("khong-ton-tai", "password")


def test_username_rong_nem_unauthorized():
    use_case, _ = make_use_case()
    with pytest.raises(UnauthorizedError):
        use_case.execute("", "password")
    with pytest.raises(UnauthorizedError):
        use_case.execute("   ", "password")


def test_password_rong_nem_unauthorized():
    use_case, _ = make_use_case()
    with pytest.raises(UnauthorizedError):
        use_case.execute("sinhvien01", "")


def test_khong_tiet_lo_buoc_sai_tai_thong_diep():
    """Mọi fail đều cùng một thông điệp — không lộ sai ở bước nào."""
    msg = "Sai tài khoản hoặc mật khẩu"
    uc1, _ = make_use_case(valid=False, user=None)
    uc2, _ = make_use_case(valid=True, user=None)
    with pytest.raises(UnauthorizedError) as e1:
        uc1.execute("u", "p")
    with pytest.raises(UnauthorizedError) as e2:
        uc2.execute("u", "p")
    assert e1.value.message == msg
    assert e2.value.message == msg
