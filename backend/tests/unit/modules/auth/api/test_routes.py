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
    assert body["user_id"] == "u-001"
    assert body["role"] == "student"
