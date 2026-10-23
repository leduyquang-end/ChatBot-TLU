import pytest

from src.shared.common.errors import ConfigError
from src.shared.config.settings import Settings, get_settings, reset_settings_cache

_REQUIRED = [
    "GROQ_API_KEY",
    "QWEN_API_KEY",
    "HF_TOKEN",
    "CHROMA_URL",
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
]


@pytest.fixture(autouse=True)
def _fresh_settings():
    reset_settings_cache()
    yield
    reset_settings_cache()


def set_required(monkeypatch) -> None:
    for name in _REQUIRED:
        monkeypatch.setenv(name, "gia-thu")


def test_thieu_bien_bat_buoc_dung_khoi_dong(monkeypatch):
    for name in _REQUIRED:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ConfigError):
        Settings.from_env()


def test_thieu_bien_bao_ro_ten_bien(monkeypatch):
    for name in _REQUIRED:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ConfigError, match="GROQ_API_KEY"):
        Settings.from_env()


def test_gia_tri_mac_dinh_khong_bat_buoc(monkeypatch):
    set_required(monkeypatch)
    for name in (
        "APP_PORT",
        "LOG_LEVEL",
        "DATABASE_URL",
        "REFRESH_TOKEN_TTL_HOURS",
        "ANSWER_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    settings = Settings.from_env()
    assert settings.app_port == 8000
    assert settings.refresh_token_ttl_hours == 720
    assert settings.log_level == "INFO"
    assert settings.database_url == "sqlite:///data/chatbot_tlu.db"
    assert settings.answer_model == "qwen3-235b-a22b"


def test_app_port_sai_so_nem_config_error(monkeypatch):
    set_required(monkeypatch)
    monkeypatch.setenv("APP_PORT", "khong-phai-so")
    with pytest.raises(ConfigError, match="APP_PORT"):
        Settings.from_env()


def test_bien_bat_buoc_toan_khoang_trang_nem_config_error(monkeypatch):
    set_required(monkeypatch)
    monkeypatch.setenv("GROQ_API_KEY", "   ")
    with pytest.raises(ConfigError, match="GROQ_API_KEY"):
        Settings.from_env()


def test_env_float_sai_nem_config_error(monkeypatch):
    set_required(monkeypatch)
    monkeypatch.setenv("ALPHA", "khong-phai-so")
    with pytest.raises(ConfigError, match="ALPHA"):
        Settings.from_env()


def test_env_so_de_trong_dung_mac_dinh(monkeypatch):
    set_required(monkeypatch)
    monkeypatch.setenv("TOP_K", "")
    monkeypatch.setenv("ALPHA", " ")
    settings = Settings.from_env()
    assert settings.top_k == 5
    assert settings.alpha == 0.7


def test_url_bo_gach_cheo_cuoi(monkeypatch):
    set_required(monkeypatch)
    monkeypatch.setenv("CHROMA_URL", "http://localhost:8001/")
    monkeypatch.setenv("QWEN_BASE_URL", "https://x.test/v1//")
    settings = Settings.from_env()
    assert settings.chroma_url == "http://localhost:8001"
    assert settings.qwen_base_url == "https://x.test/v1"


def test_log_level_duoc_chu_hoa(monkeypatch):
    set_required(monkeypatch)
    monkeypatch.setenv("LOG_LEVEL", "debug")
    assert Settings.from_env().log_level == "DEBUG"


def test_database_url_tuy_chon_dat_duoc(monkeypatch):
    set_required(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp/x.db")
    assert Settings.from_env().database_url == "sqlite:///tmp/x.db"


def test_get_settings_ghi_nho(monkeypatch):
    set_required(monkeypatch)
    assert get_settings() is get_settings()
