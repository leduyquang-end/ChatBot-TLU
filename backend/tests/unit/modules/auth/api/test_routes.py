import pytest

from src.main import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_login_thieu_username(client):
    resp = client.post("/auth/login", json={"password": "demo-password"})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_thieu_password(client):
    resp = client.post("/auth/login", json={"username": "sinhvien01"})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_password_khong_phai_string(client):
    resp = client.post("/auth/login", json={"username": "sinhvien01", "password": 12345})
    assert resp.status_code == 400


def test_login_sai_mat_khau(client):
    resp = client.post(
        "/auth/login", json={"username": "sinhvien01", "password": "sai-mat-khau"}
    )
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_login_thanh_cong(client):
    resp = client.post(
        "/auth/login",
        json={"username": "sinhvien01", "password": "demo-password"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["token"]
    assert body["refresh_token"]
    assert body["user_id"] == "u-001"
    assert body["role"] == "student"


def login(client) -> dict:
    resp = client.post(
        "/auth/login",
        json={"username": "sinhvien01", "password": "demo-password"},
    )
    assert resp.status_code == 200
    return resp.get_json()


def test_refresh_thieu_refresh_token(client):
    resp = client.post("/auth/refresh", json={})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_refresh_phien_khong_hop_le(client):
    resp = client.post("/auth/refresh", json={"refresh_token": "khong-ton-tai"})
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_refresh_thanh_cong_xoay_phien(client):
    body = login(client)
    resp = client.post("/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert resp.status_code == 200
    new = resp.get_json()
    assert new["token"]
    assert new["user_id"] == "u-001"
    # Xoay phiên: chuỗi refresh mới phải khác chuỗi cũ
    assert new["refresh_token"] != body["refresh_token"]


def test_logout_thieu_refresh_token(client):
    resp = client.post("/auth/logout", json={})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_logout_khong_phai_string(client):
    resp = client.post("/auth/logout", json={"refresh_token": 123})
    assert resp.status_code == 400


def test_logout_thanh_cong_va_phien_het_hieu_luc(client):
    body = login(client)

    resp = client.post("/auth/logout", json={"refresh_token": body["refresh_token"]})
    assert resp.status_code == 200
    assert resp.get_json()["revoked"] is True

    # Đã đăng xuất → dùng chuỗi refresh cũ để refresh → 401
    resp2 = client.post("/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert resp2.status_code == 401


def test_logout_phien_khong_ton_tai_van_200(client):
    resp = client.post("/auth/logout", json={"refresh_token": "khong-ton-tai"})
    assert resp.status_code == 200
    assert resp.get_json()["revoked"] is False
