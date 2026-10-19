from datetime import UTC, datetime, timedelta

from src.modules.auth.infrastructure.in_memory_refresh_token_store import (
    InMemoryRefreshTokenStore,
)

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def make_store(*, ttl_seconds: int = 3600) -> InMemoryRefreshTokenStore:
    return InMemoryRefreshTokenStore(ttl_seconds=ttl_seconds, now_fn=lambda: NOW)


def test_create_tra_phien_dung_han_va_tim_duoc():
    store = make_store(ttl_seconds=60)
    session = store.create("u-001")
    assert session.user_id == "u-001"
    assert session.issued_at == NOW
    assert session.expires_at == NOW + timedelta(seconds=60)
    assert store.find(session.token) is session


def test_create_lan_hai_tao_chuoi_khac_nhau():
    store = make_store()
    a = store.create("u-001")
    b = store.create("u-001")
    assert a.token != b.token


def test_find_chuoi_la_tra_none():
    store = make_store()
    assert store.find("khong-ton-tai") is None


def test_revoke_xoa_phien_va_revoke_lai_van_an_toan():
    store = make_store()
    session = store.create("u-001")
    store.revoke(session.token)
    assert store.find(session.token) is None
    store.revoke(session.token)  # idempotent — không ném lỗi


def test_store_khong_tu_het_han_lam_het_han_la_nghiep_vu_cua_domain():
    """Store quá hạn vẫn find được — việc quyết định "hết hạn" là của RefreshToken.is_expired."""
    store = make_store(ttl_seconds=60)
    session = store.create("u-001")
    assert store.find(session.token) is not None
    assert session.is_expired(NOW + timedelta(seconds=61)) is True


def test_singleton_tra_cung_mot_object(monkeypatch):
    """get_refresh_token_store() phải trả cùng một object (phiên sống qua nhiều request)."""
    from src.modules.auth.infrastructure import in_memory_refresh_token_store as mod

    existing = InMemoryRefreshTokenStore(ttl_seconds=60)
    monkeypatch.setattr(mod, "_STORE", existing)
    assert mod.get_refresh_token_store() is existing
