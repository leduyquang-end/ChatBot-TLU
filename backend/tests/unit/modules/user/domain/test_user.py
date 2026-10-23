import pytest

from src.modules.user.domain.user import (
    FULL_NAME_MAX_LENGTH,
    ROLE_ADMIN,
    ROLE_STUDENT,
    User,
)
from src.shared.common.errors import ValidationError

STUDENT = User(
    id="u-001", username="sinhvien01", full_name="Sinh viên Demo", role=ROLE_STUDENT
)
ADMIN = User(id="u-002", username="admin01", full_name="Quản trị", role=ROLE_ADMIN)


def test_tao_user_hop_le():
    assert STUDENT.id == "u-001"
    assert STUDENT.role == ROLE_STUDENT
    assert not STUDENT.is_admin()
    assert ADMIN.is_admin()


def test_role_khong_hop_le_nem_value_error():
    with pytest.raises(ValueError, match="Vai trò không hợp lệ"):
        User(id="u-9", username="x", full_name="X", role="guest")


def test_ho_ten_rong_khi_tao_nem_value_error():
    with pytest.raises(ValueError, match="Họ và tên"):
        User(id="u-9", username="x", full_name="", role=ROLE_STUDENT)
    with pytest.raises(ValueError, match="Họ và tên"):
        User(id="u-9", username="x", full_name="   ", role=ROLE_STUDENT)


def test_ho_ten_qua_dai_khi_tao_nem_value_error():
    with pytest.raises(ValueError, match=str(FULL_NAME_MAX_LENGTH)):
        User(id="u-9", username="x", full_name="A" * 101, role=ROLE_STUDENT)


def test_ho_ten_100_ky_tu_tao_duoc():
    user = User(id="u-9", username="x", full_name="A" * 100, role=ROLE_STUDENT)
    assert user.full_name == "A" * 100


def test_with_full_name_tra_ban_moi_va_giu_ban_cu():
    updated = STUDENT.with_full_name("Nguyễn Văn A")
    assert updated.full_name == "Nguyễn Văn A"
    assert updated.id == STUDENT.id
    assert updated.username == STUDENT.username
    assert updated.role == STUDENT.role
    assert STUDENT.full_name == "Sinh viên Demo"


def test_with_full_name_cat_khoang_trang():
    assert STUDENT.with_full_name("  Trần Thị B  ").full_name == "Trần Thị B"


def test_with_full_name_rong_nem_validation_400():
    with pytest.raises(ValidationError) as exc:
        STUDENT.with_full_name("   ")
    assert exc.value.http_status == 400


def test_with_full_name_qua_dai_nem_validation_400():
    with pytest.raises(ValidationError) as exc:
        STUDENT.with_full_name("A" * 101)
    assert exc.value.http_status == 400
    assert str(FULL_NAME_MAX_LENGTH) in exc.value.message
