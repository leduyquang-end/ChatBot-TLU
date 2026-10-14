import pytest

from src.shared.common.errors import ConfigError, ValidationError
from src.shared.config.settings import Settings


def test_thieu_bien_bat_buoc_dung_khoi_dong():
    with pytest.raises(ConfigError):
        Settings.from_env()


def test_validation_error_co_http_400():
    err = ValidationError("Sai")
    assert err.http_status == 400
    assert err.code == "VALIDATION_ERROR"
