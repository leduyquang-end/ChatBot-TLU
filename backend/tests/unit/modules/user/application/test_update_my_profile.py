import pytest

from src.modules.user.application.update_my_profile import UpdateMyProfile
from src.shared.common.errors import NotFoundError, ValidationError
from tests.unit.modules.user.application.fakes import DEMO_USER, FakeUserRepository


def test_cap_nhat_ho_ten_thanh_cong():
    repo = FakeUserRepository([DEMO_USER])
    use_case = UpdateMyProfile(repo)
    user = use_case.execute("u-001", "Nguyễn Văn A")
    assert user.full_name == "Nguyễn Văn A"
    assert user.id == "u-001"
    assert user.username == "sinhvien01"
    assert user.role == "student"
    assert repo.saved == [user]


def test_ho_ten_bi_cat_khoang_trang():
    use_case = UpdateMyProfile(FakeUserRepository([DEMO_USER]))
    user = use_case.execute("u-001", "   Trần Thị B   ")
    assert user.full_name == "Trần Thị B"


def test_ho_ten_100_ky_tu_van_chap_nhan():
    use_case = UpdateMyProfile(FakeUserRepository([DEMO_USER]))
    user = use_case.execute("u-001", "A" * 100)
    assert user.full_name == "A" * 100


def test_khong_thay_user_nem_not_found_404():
    use_case = UpdateMyProfile(FakeUserRepository())
    with pytest.raises(NotFoundError) as exc:
        use_case.execute("khong-ton-tai", "Nguyễn Văn A")
    assert exc.value.http_status == 404


def test_ho_ten_rong_nem_validation_400():
    use_case = UpdateMyProfile(FakeUserRepository([DEMO_USER]))
    with pytest.raises(ValidationError) as exc:
        use_case.execute("u-001", "")
    assert exc.value.http_status == 400
    with pytest.raises(ValidationError):
        use_case.execute("u-001", "   ")


def test_ho_ten_qua_dai_nem_validation_400():
    use_case = UpdateMyProfile(FakeUserRepository([DEMO_USER]))
    with pytest.raises(ValidationError) as exc:
        use_case.execute("u-001", "A" * 101)
    assert "100" in exc.value.message


def test_full_name_bien_dong_khong_bi_thay_doi():
    """User là frozen dataclass — bản cũ không bị đổi ngầm."""
    repo = FakeUserRepository([DEMO_USER])
    UpdateMyProfile(repo).execute("u-001", "Nguyễn Văn A")
    assert DEMO_USER.full_name == "Sinh viên Demo"
