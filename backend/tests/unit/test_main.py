from src.main import create_app


def test_route_khong_ton_tai_tra_404_json():
    client = create_app().test_client()

    response = client.get("/khong-ton-tai")

    assert response.status_code == 404
    body = response.get_json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"]
