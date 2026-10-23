import pytest

from src.modules.user.application.change_password import ChangePassword
from src.shared.common.errors import NotFoundError, UnauthorizedError, ValidationError
from src.shared.events import EventBus, UserPasswordChanged
from tests.unit.modules.user.application.fakes import DEMO_USER, FakeUserRepository

OLD_PASSWORD = "mat-khau-cu-1"


def make_repo() -> FakeUserRepository:
    repo = FakeUserRepository([DEMO_USER])
    repo.passwords[DEMO_USER.username] = OLD_PASSWORD
    return repo


def test_doi_mat_khau_thanh_cong():
    repo = make_repo()
    use_case = ChangePassword(repo, EventBus())
    result = use_case.execute("u-001", OLD_PASSWORD, "mat-khau-moi-1")
    assert result is None
    assert repo.passwords[DEMO_USER.username] == "mat-khau-moi-1"
    assert repo.set_password_calls == [(DEMO_USER.username, "mat-khau-moi-1")]


def test_sai_mat_khau_cu_nem_unauthorized_401():
    repo = make_repo()
    use_case = ChangePassword(repo, EventBus())
    with pytest.raises(UnauthorizedError) as exc:
        use_case.execute("u-001", "sai-het", "mat-khau-moi-1")
    assert exc.value.http_status == 401
    assert exc.value.message == "Mật khẩu cũ không đúng"
    assert repo.set_password_calls == []


def test_mat_khau_moi_qua_ngan_nem_validation_400():
    repo = make_repo()
    use_case = ChangePassword(repo, EventBus())
    with pytest.raises(ValidationError) as exc:
        use_case.execute("u-001", OLD_PASSWORD, "abc12")
    assert exc.value.http_status == 400
    assert repo.set_password_calls == []


def test_mat_khau_moi_qua_dai_nem_validation_400():
    repo = make_repo()
    use_case = ChangePassword(repo, EventBus())
    with pytest.raises(ValidationError):
        use_case.execute("u-001", OLD_PASSWORD, "a" * 129)
    assert repo.set_password_calls == []


def test_mat_khau_moi_giong_cu_nem_validation_400():
    repo = make_repo()
    use_case = ChangePassword(repo, EventBus())
    with pytest.raises(ValidationError) as exc:
        use_case.execute("u-001", OLD_PASSWORD, OLD_PASSWORD)
    assert "khác" in exc.value.message
    assert repo.set_password_calls == []


def test_khong_thay_user_nem_not_found_404():
    repo = FakeUserRepository()
    use_case = ChangePassword(repo, EventBus())
    with pytest.raises(NotFoundError) as exc:
        use_case.execute("khong-ton-tai", OLD_PASSWORD, "mat-khau-moi-1")
    assert exc.value.http_status == 404
    assert repo.set_password_calls == []


def test_doi_mat_khau_phat_su_kien_user_password_changed():
    bus = EventBus()
    received: list[UserPasswordChanged] = []
    bus.subscribe(UserPasswordChanged, received.append)

    ChangePassword(make_repo(), bus).execute("u-001", OLD_PASSWORD, "mat-khau-moi-1")

    assert received == [UserPasswordChanged(user_id="u-001")]


def test_doi_mat_khau_that_bai_khong_phat_su_kien():
    bus = EventBus()
    received: list[UserPasswordChanged] = []
    bus.subscribe(UserPasswordChanged, received.append)

    with pytest.raises(UnauthorizedError):
        ChangePassword(make_repo(), bus).execute("u-001", "sai-het", "mat-khau-moi-1")

    assert received == []
