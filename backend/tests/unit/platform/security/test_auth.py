import hashlib
import hmac
import logging
import time

import pytest

from src.platform.security import auth as auth_mod
from src.platform.security.auth import (
    hash_password,
    issue_token,
    require_role,
    sanitize_input,
    verify_password,
    verify_token,
)
from src.shared.common.errors import ForbiddenError, UnauthorizedError

FIXED_SALT = b"\x01" * 16
SECRET = "bi-mat-test-0123456789"


# --- mật khẩu ---


def test_hash_verify_dung_sai():
    stored = hash_password("mat-khau-1")
    assert verify_password("mat-khau-1", stored) is True
    assert verify_password("sai-mat-khau", stored) is False


def test_hash_khong_luu_plaintext():
    stored = hash_password("mat-khau-goc-123")
    assert "mat-khau-goc-123" not in stored
    salt_hex, _digest = stored.split("$", 1)
    assert len(salt_hex) == 32


def test_salt_ngau_nhien_lam_hash_khac_nhau():
    assert hash_password("cung-mat-khau") != hash_password("cung-mat-khau")


def test_salt_tuy_chon_lam_hash_giong_nhau():
    assert hash_password("pw", salt=FIXED_SALT) == hash_password("pw", salt=FIXED_SALT)


def test_verify_sai_dinh_dang_stored_tra_false_khong_loi():
    for stored in ("", "khong-phai-hash", "aa$zz", "$$"):
        assert verify_password("pw", stored) is False


def test_mat_khau_dai_bi_cat_nhat_quan():
    """PBKDF2 không được tính trên chuỗi dài bất thường — hash lẫn verify cắt cùng nhau."""
    long_password = "x" * 5000
    stored = hash_password(long_password, salt=FIXED_SALT)
    assert stored == hash_password(long_password[:1024], salt=FIXED_SALT)
    assert verify_password(long_password, stored) is True
    assert verify_password(long_password[:1024], stored) is True


# --- token ---


def test_issue_verify_tra_lai_user_id():
    token = issue_token("u-001", ttl_seconds=3600)
    assert verify_token(token) == "u-001"


def test_token_het_han_bi_tu_choi():
    token = issue_token("u-001", ttl_seconds=-1)
    with pytest.raises(UnauthorizedError) as exc:
        verify_token(token)
    assert "hết hạn" in exc.value.message


def test_token_sai_ky_ten_bi_tu_choi():
    with pytest.raises(UnauthorizedError):
        verify_token("sai.token.khac")
    with pytest.raises(UnauthorizedError):
        verify_token("khong-du-hai-dau-cham")


def test_token_ky_tu_khong_ascii_tra_401_khong_phai_500():
    """Hồi quy: compare_digest ném TypeError với chuỗi không ASCII → trước là 500."""
    with pytest.raises(UnauthorizedError) as exc:
        verify_token("u-1.99999999999.không-phải-hex")
    assert exc.value.http_status == 401


def test_token_expires_khong_phai_so_tra_401(monkeypatch):
    monkeypatch.setenv("APP_SECRET", SECRET)
    payload = "u-1.khong-phai-so"
    sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    with pytest.raises(UnauthorizedError):
        verify_token(f"{payload}.{sig}")


def test_token_duoc_doi_payload_bi_bat_truoc_khi_kiem_het_han(monkeypatch):
    """Chữ ký kiểm tra trước — field expires sửa bị coi là không hợp lệ, không phải hết hạn."""
    monkeypatch.setenv("APP_SECRET", SECRET)
    expired = issue_token("u-1", ttl_seconds=-10)
    user_id, _old_expires, sig = expired.rsplit(".", 2)
    forged_payload = f"{user_id}.{int(time.time()) + 99999}"
    with pytest.raises(UnauthorizedError) as exc:
        verify_token(f"{forged_payload}.{sig}")
    assert "hợp lệ" in exc.value.message


# --- phân quyền ---


def test_require_role_du_quyen_khong_loi():
    require_role("admin", {"admin"})
    require_role("student", {"student", "admin"})


def test_require_role_thieu_quyen_tra_403():
    with pytest.raises(ForbiddenError) as exc:
        require_role("student", {"admin"})
    assert exc.value.http_status == 403
    assert exc.value.code == "FORBIDDEN"


# --- làm sạch đầu vào ---


def test_sanitize_loai_ky_tu_dieu_khien():
    assert sanitize_input("a\x00\x07b", max_length=100) == "ab"


def test_sanitize_giu_xuong_dong_tab():
    assert sanitize_input("a\nb\tc", max_length=100) == "a\nb\tc"


def test_sanitize_bot_khoang_trang_dau_cuoi():
    assert sanitize_input("   chữ   ", max_length=100) == "chữ"


def test_sanitize_cat_do_dai():
    assert sanitize_input("a" * 105, max_length=100) == "a" * 100


def test_sanitize_khoang_trang_do_bi_cat_khong_con_sot():
    text = "b" * 99 + " " + "c" * 50
    cleaned = sanitize_input(text, max_length=100)
    assert cleaned == "b" * 99


# --- APP_SECRET ---


def test_canh_bao_khi_thieu_app_secret(monkeypatch, caplog):
    monkeypatch.delenv("APP_SECRET", raising=False)
    monkeypatch.setattr(auth_mod, "_secret_warnings", set())
    with caplog.at_level(logging.WARNING, logger="src.platform.security.auth"):
        auth_mod.issue_token("u-9")
    assert any("security.default_secret" in rec.getMessage() for rec in caplog.records)


def test_canh_bao_khi_app_secret_chi_co_khoang_trang(monkeypatch, caplog):
    monkeypatch.setenv("APP_SECRET", "   ")
    monkeypatch.setattr(auth_mod, "_secret_warnings", set())
    with caplog.at_level(logging.WARNING, logger="src.platform.security.auth"):
        auth_mod.issue_token("u-9")
    assert any("security.default_secret" in rec.getMessage() for rec in caplog.records)


def test_canh_bao_khi_app_secret_qua_ngan(monkeypatch, caplog):
    monkeypatch.setenv("APP_SECRET", "ngan-qua")
    monkeypatch.setattr(auth_mod, "_secret_warnings", set())
    with caplog.at_level(logging.WARNING, logger="src.platform.security.auth"):
        auth_mod.issue_token("u-9")
    assert any("security.weak_secret" in rec.getMessage() for rec in caplog.records)


def test_khong_canh_bao_khi_co_app_secret_du_manh(monkeypatch, caplog):
    monkeypatch.setenv("APP_SECRET", SECRET)
    monkeypatch.setattr(auth_mod, "_secret_warnings", set())
    with caplog.at_level(logging.WARNING, logger="src.platform.security.auth"):
        auth_mod.issue_token("u-9")
    assert not any("security." in rec.getMessage() for rec in caplog.records)
