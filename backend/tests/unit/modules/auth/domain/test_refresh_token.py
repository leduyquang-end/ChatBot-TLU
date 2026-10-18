from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from src.modules.auth.domain.refresh_token import RefreshToken

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

TOKEN = RefreshToken(
    token="raw-token",
    user_id="u-001",
    issued_at=NOW,
    expires_at=NOW + timedelta(hours=1),
)


def test_chua_het_han_truoc_moc_het_han():
    assert TOKEN.is_expired(NOW) is False
    assert TOKEN.is_expired(NOW + timedelta(minutes=59)) is False


def test_het_han_dung_tai_moc_het_han():
    """Tại đúng mốc hết hạn → coi là hết hạn (expires_at là mốc đóng)."""
    assert TOKEN.is_expired(NOW + timedelta(hours=1)) is True


def test_het_han_sau_moc_het_han():
    assert TOKEN.is_expired(NOW + timedelta(hours=2)) is True


def test_phien_bat_bien_khong_sua_duoc():
    with pytest.raises(FrozenInstanceError):
        TOKEN.user_id = "u-999"  # type: ignore[misc]
