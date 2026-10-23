import pytest

from src.modules.user.domain.password_rules import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    ensure_password_changed,
    validate_password_format,
)
from src.shared.common.errors import ValidationError


def test_mat_khau_du_do_dai_chap_nhan():
    validate_password_format("a" * PASSWORD_MIN_LENGTH)
    validate_password_format("a" * PASSWORD_MAX_LENGTH)


def test_mat_khau_qua_ngan_nem_validation_400():
    with pytest.raises(ValidationError) as exc:
        validate_password_format("a" * (PASSWORD_MIN_LENGTH - 1))
    assert exc.value.http_status == 400
    assert str(PASSWORD_MIN_LENGTH) in exc.value.message
    assert str(PASSWORD_MAX_LENGTH) in exc.value.message


def test_mat_khau_qua_dai_nem_validation_400():
    with pytest.raises(ValidationError):
        validate_password_format("a" * (PASSWORD_MAX_LENGTH + 1))


def test_mat_khau_moi_khac_cu_khong_loi():
    ensure_password_changed("mat-khau-cu", "mat-khau-moi")


def test_mat_khau_moi_trung_cu_nem_validation_400():
    with pytest.raises(ValidationError) as exc:
        ensure_password_changed("mat-khau-cu", "mat-khau-cu")
    assert exc.value.http_status == 400
    assert "khác" in exc.value.message
