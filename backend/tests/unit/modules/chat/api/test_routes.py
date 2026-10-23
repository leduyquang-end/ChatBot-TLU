import pytest

import src.modules.chat.api.routes as chat_routes
from src.main import create_app
from src.platform.security.auth import issue_token


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def auth_header(user_id: str = "u-test") -> dict:
    return {"Authorization": f"Bearer {issue_token(user_id)}"}


class StubPipeline:
    def ask(self, *, user_id: str, conversation_id: str, question: str) -> dict:
        return {
            "answer": "Câu trả lời từ tài liệu.",
            "mode": "Vector",
            "conversation_id": conversation_id,
            "sources": ["QĐ-01"],
        }

    def history(self, *, user_id: str, conversation_id: str) -> list[dict]:
        if conversation_id == "c-own" and user_id == "u-test":
            return [{"role": "user", "content": "Xin chào"}]
        return []


def test_e3_cau_hoi_rong_tra_400(client):
    resp = client.post(
        "/chat/ask", json={"question": "   "}, headers=auth_header()
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_e3_cau_hoi_chi_ky_tu_dac_biet_tra_400(client):
    resp = client.post(
        "/chat/ask", json={"question": "!!! ??? ..."}, headers=auth_header()
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_e7_chua_dang_nhap_tra_401(client):
    resp = client.post("/chat/ask", json={"question": "Học phí bao nhiêu?"})
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_e7_token_sai_tra_401(client):
    resp = client.post(
        "/chat/ask",
        json={"question": "Học phí bao nhiêu?"},
        headers={"Authorization": "Bearer sai.token.khac"},
    )
    assert resp.status_code == 401


def test_history_chua_dang_nhap_tra_401(client):
    resp = client.get("/chat/history?conversation_id=c1")
    assert resp.status_code == 401


def test_history_thieu_conversation_id_tra_400(client):
    resp = client.get("/chat/history", headers=auth_header())
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_ask_thanh_cong_voi_fake_pipeline(client, monkeypatch):
    monkeypatch.setattr(chat_routes, "_build_pipeline", lambda: StubPipeline())
    resp = client.post(
        "/chat/ask",
        json={"question": "Học phí bao nhiêu?"},
        headers=auth_header(),
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["answer"] == "Câu trả lời từ tài liệu."
    assert body["mode"] == "Vector"
    assert body["conversation_id"]
    assert body["sources"] == ["QĐ-01"]


def test_ask_gui_conversation_id_cu(client, monkeypatch):
    monkeypatch.setattr(chat_routes, "_build_pipeline", lambda: StubPipeline())
    resp = client.post(
        "/chat/ask",
        json={"question": "Học phí bao nhiêu?", "conversation_id": "c-123"},
        headers=auth_header(),
    )
    assert resp.status_code == 200
    assert resp.get_json()["conversation_id"] == "c-123"


def test_history_chinh_minh_co_du_lieu(client, monkeypatch):
    monkeypatch.setattr(chat_routes, "_build_pipeline", lambda: StubPipeline())
    resp = client.get(
        "/chat/history?conversation_id=c-own", headers=auth_header()
    )
    assert resp.status_code == 200
    assert resp.get_json()["turns"] != []


def test_history_nguoi_khac_bi_tu_choi(client, monkeypatch):
    """Không trả về lịch sử của người khác (mục 5.5, 11.2)."""
    monkeypatch.setattr(chat_routes, "_build_pipeline", lambda: StubPipeline())
    resp = client.get(
        "/chat/history?conversation_id=c-own", headers=auth_header("u-khac")
    )
    assert resp.status_code == 200
    assert resp.get_json()["turns"] == []


def test_ask_question_khong_phai_chuoi_tra_400_khong_phai_500(client):
    resp = client.post("/chat/ask", json={"question": 123}, headers=auth_header())
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_ask_body_khong_phai_object_tra_400(client):
    resp = client.post("/chat/ask", json=["khong phai object"], headers=auth_header())
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_ask_conversation_id_khong_phai_chuoi_van_tra_loi_voi_id_moi(
    client, monkeypatch
):
    monkeypatch.setattr(chat_routes, "_build_pipeline", lambda: StubPipeline())
    resp = client.post(
        "/chat/ask",
        json={"question": "Học phí bao nhiêu?", "conversation_id": 999},
        headers=auth_header(),
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["conversation_id"] != "999"
    assert body["conversation_id"]


def test_loi_dich_vu_tra_503_thong_bao_busy(client, monkeypatch):
    """Q-04: dịch vụ lỗi → 503, người dùng thấy thông báo bận, không lộ kỹ thuật."""
    from src.modules.chat.domain.prompt import SERVICE_BUSY_MESSAGE
    from src.shared.common.errors import ExternalServiceError

    class BusyPipeline:
        def ask(self, *, user_id, conversation_id, question):
            raise ExternalServiceError(SERVICE_BUSY_MESSAGE)

        def history(self, *, user_id, conversation_id):
            return []

    monkeypatch.setattr(chat_routes, "_build_pipeline", lambda: BusyPipeline())
    resp = client.post(
        "/chat/ask", json={"question": "Học phí bao nhiêu?"}, headers=auth_header()
    )
    assert resp.status_code == 503
    body = resp.get_json()
    assert body["error"]["code"] == "EXTERNAL_SERVICE_ERROR"
    assert body["error"]["message"] == SERVICE_BUSY_MESSAGE
