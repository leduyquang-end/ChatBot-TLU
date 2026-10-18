from datetime import UTC, datetime, timedelta

from src.modules.auth.application.logout import LogoutResult, LogoutUseCase
from src.modules.auth.domain.refresh_token import RefreshToken

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class FakeStore:
    def __init__(self) -> None:
        self.sessions: dict[str, RefreshToken] = {}
        self.revoked: list[str] = []
        self._seq = 0

    def create(self, user_id: str) -> RefreshToken:
        self._seq += 1
        session = RefreshToken(
            token=f"rt-{self._seq}",
            user_id=user_id,
            issued_at=NOW,
            expires_at=NOW + timedelta(days=30),
        )
        self.sessions[session.token] = session
        return session

    def find(self, raw_token: str) -> RefreshToken | None:
        return self.sessions.get(raw_token)

    def revoke(self, raw_token: str) -> None:
        self.revoked.append(raw_token)
        self.sessions.pop(raw_token, None)


def test_logout_thanh_cong_thu_hoi_phien():
    store = FakeStore()
    session = store.create("u-001")

    result = LogoutUseCase(store=store).execute(session.token)

    assert isinstance(result, LogoutResult)
    assert result.revoked is True
    assert store.find(session.token) is None
    assert store.revoked == [session.token]


def test_logout_phien_khong_ton_tai_van_thanh_cong():
    """Idempotent: chuỗi lạ → revoked=False, không ném lỗi."""
    store = FakeStore()
    result = LogoutUseCase(store=store).execute("khong-ton-tai")
    assert result.revoked is False
    assert store.revoked == []


def test_logout_lan_hai_khong_sai_nua():
    store = FakeStore()
    session = store.create("u-001")
    use_case = LogoutUseCase(store=store)

    first = use_case.execute(session.token)
    second = use_case.execute(session.token)

    assert first.revoked is True
    assert second.revoked is False


def test_logout_chuoi_rong_tra_false():
    store = FakeStore()
    assert LogoutUseCase(store=store).execute("").revoked is False
    assert LogoutUseCase(store=store).execute("   ").revoked is False
