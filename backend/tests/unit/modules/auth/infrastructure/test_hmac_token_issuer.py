from src.modules.auth.infrastructure.hmac_token_issuer import HmacTokenIssuer
from src.platform.security.auth import verify_token


def test_issue_tao_token_verify_duoc(monkeypatch):
    monkeypatch.setenv("APP_SECRET", "secret-du-dai-cho-test-123456")
    token = HmacTokenIssuer().issue("u-001")
    assert verify_token(token) == "u-001"


def test_token_khac_user_khac(monkeypatch):
    monkeypatch.setenv("APP_SECRET", "secret-du-dai-cho-test-123456")
    issuer = HmacTokenIssuer()
    assert verify_token(issuer.issue("u-001")) != verify_token(issuer.issue("u-002"))
