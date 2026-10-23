import pytest

from src.modules.user.application.get_user_by_id import GetUserById
from src.shared.common.errors import NotFoundError
from tests.unit.modules.user.application.fakes import DEMO_USER, FakeUserRepository


def test_tim_thay_tra_ve_user():
    use_case = GetUserById(FakeUserRepository([DEMO_USER]))
    user = use_case.execute("u-001")
    assert user == DEMO_USER
    assert user.username == "sinhvien01"


def test_khong_thay_nem_not_found_404():
    use_case = GetUserById(FakeUserRepository())
    with pytest.raises(NotFoundError) as exc:
        use_case.execute("khong-ton-tai")
    assert exc.value.code == "NOT_FOUND"
    assert exc.value.http_status == 404
