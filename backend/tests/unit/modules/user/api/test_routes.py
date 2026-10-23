import pytest

from src.main import create_app
from src.modules.user.infrastructure.in_memory_user_repository import (
    reset_user_repository,
)


@pytest.fixture()
def client():
    reset_user_repository()
    app = create_app()
    app.config["TESTING"] = True
    yield app.test_client()
    reset_user_repository()


def login(client, username: str = "sinhvien01", password: str = "demo-password") -> dict:
    resp = client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200
    return resp.get_json()


def auth_headers(body: dict) -> dict:
    return {"Authorization": f"Bearer {body['token']}"}


def test_me_khong_dang_nhap_401(client):
    resp = client.get("/user/me")
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_me_token_sai_401(client):
    resp = client.get("/user/me", headers={"Authorization": "Bearer sai.token.day"})
    assert resp.status_code == 401


def test_me_tra_thong_tin_user(client):
    body = login(client)
    resp = client.get("/user/me", headers=auth_headers(body))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "id": "u-001",
        "username": "sinhvien01",
        "full_name": "Sinh viên Demo",
        "role": "student",
    }


def test_cap_nhat_ho_ten_thanh_cong(client):
    body = login(client)
    resp = client.put(
        "/user/me", json={"full_name": "  Nguyễn Văn A  "}, headers=auth_headers(body)
    )
    assert resp.status_code == 200
    assert resp.get_json()["full_name"] == "Nguyễn Văn A"

    me = client.get("/user/me", headers=auth_headers(body)).get_json()
    assert me["full_name"] == "Nguyễn Văn A"


def test_cap_nhat_thieu_ho_ten_400(client):
    body = login(client)
    resp = client.put("/user/me", json={}, headers=auth_headers(body))
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_cap_nhat_ho_ten_khong_phai_chuoi_400(client):
    body = login(client)
    resp = client.put("/user/me", json={"full_name": 123}, headers=auth_headers(body))
    assert resp.status_code == 400


def test_cap_nhat_ho_ten_rong_400(client):
    body = login(client)
    resp = client.put("/user/me", json={"full_name": "   "}, headers=auth_headers(body))
    assert resp.status_code == 400


def test_cap_nhat_ho_ten_qua_dai_400(client):
    body = login(client)
    resp = client.put(
        "/user/me", json={"full_name": "A" * 101}, headers=auth_headers(body)
    )
    assert resp.status_code == 400


def test_doi_mat_khau_thanh_cong(client):
    body = login(client)
    resp = client.post(
        "/user/change-password",
        json={"old_password": "demo-password", "new_password": "mat-khau-moi-123"},
        headers=auth_headers(body),
    )
    assert resp.status_code == 200
    assert resp.get_json()["changed"] is True

    login(client, password="mat-khau-moi-123")
    old = client.post(
        "/auth/login", json={"username": "sinhvien01", "password": "demo-password"}
    )
    assert old.status_code == 401


def test_doi_mat_khau_cu_sai_401(client):
    body = login(client)
    resp = client.post(
        "/user/change-password",
        json={"old_password": "sai-mat-khau", "new_password": "mat-khau-moi-123"},
        headers=auth_headers(body),
    )
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_doi_mat_khau_moi_trung_cu_400(client):
    body = login(client)
    resp = client.post(
        "/user/change-password",
        json={"old_password": "demo-password", "new_password": "demo-password"},
        headers=auth_headers(body),
    )
    assert resp.status_code == 400


def test_doi_mat_khau_moi_ngan_400(client):
    body = login(client)
    resp = client.post(
        "/user/change-password",
        json={"old_password": "demo-password", "new_password": "123"},
        headers=auth_headers(body),
    )
    assert resp.status_code == 400


def test_doi_mat_khau_thieu_field_400(client):
    body = login(client)
    resp = client.post(
        "/user/change-password", json={"old_password": "demo-password"},
        headers=auth_headers(body),
    )
    assert resp.status_code == 400
    resp2 = client.post(
        "/user/change-password", json={"new_password": "mat-khau-moi-123"},
        headers=auth_headers(body),
    )
    assert resp2.status_code == 400


def test_danh_sach_user_sinh_vien_bi_cam_403(client):
    body = login(client)
    resp = client.get("/user", headers=auth_headers(body))
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_danh_sach_user_admin_xem_duoc(client):
    body = login(client, username="admin01")
    resp = client.get("/user", headers=auth_headers(body))
    assert resp.status_code == 200
    users = resp.get_json()["users"]
    assert [user["id"] for user in users] == ["u-001", "u-002"]


def test_danh_sach_user_khong_dang_nhap_401(client):
    resp = client.get("/user")
    assert resp.status_code == 401
