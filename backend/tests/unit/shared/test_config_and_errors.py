import pytest

from src.shared.common.errors import ConfigError, ValidationError
from src.shared.config.settings import Settings

_REQUIRED = [
    "GROQ_API_KEY",
    "QWEN_API_KEY",
    "HF_TOKEN",
    "CHROMA_URL",
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
]


def test_thieu_bien_bat_buoc_dung_khoi_dong(monkeypatch):
    for name in _REQUIRED:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ConfigError):
        Settings.from_env()


def test_validation_error_co_http_400():
    err = ValidationError("Sai")
    assert err.http_status == 400
    assert err.code == "VALIDATION_ERROR"
