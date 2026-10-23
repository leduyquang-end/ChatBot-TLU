"""E2E hỏi đáp THẬT qua trọn luồng: auth → router → truy xuất → model trả lời.

Cần Chroma + Groq + OpenRouter cùng key thật; thiếu gì thì SKIP.
Chạy: pytest tests/integration/test_chat_e2e.py -q
"""
from __future__ import annotations

import socket
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest
from dotenv import load_dotenv

_BACKEND = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND.parent / ".env")

from src.modules.chat.domain.prompt import SERVICE_BUSY_MESSAGE
from src.shared.config.settings import get_settings

settings = get_settings()


def _tcp_up(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _url_up(url: str) -> bool:
    parsed = urlparse(url)
    return _tcp_up(parsed.hostname or "", parsed.port or (443 if parsed.scheme == "https" else 80))


@pytest.fixture(scope="module")
def e2e_client():
    # đủ điều kiện mới chạy, không thì skip toàn bộ module
    if not _tcp_up("localhost", 8001):
        pytest.skip("Chroma không mở")
    if not (settings.groq_api_key and _tcp_up("api.groq.com", 443)):
        pytest.skip("Không gọi được Groq")
    if not (settings.qwen_api_key and _url_up(settings.qwen_base_url)):
        pytest.skip("Không gọi được OpenRouter")

    from src.main import create_app
    from src.platform.security.auth import issue_token

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    auth = {"Authorization": f"Bearer {issue_token('e2e-user')}"}
    return client, auth


def _ask(client, auth, question: str, conversation_id: str | None = None):
    payload: dict = {"question": question}
    if conversation_id is not None:
        payload["conversation_id"] = conversation_id
    return client.post("/chat/ask", json=payload, headers=auth)


def _ask_with_tolerance(
    client, auth, question: str, conversation_id: str | None = None
):
    """Free-tier OpenRouter hay bão hoà: thử vài lần, vẫn 503 busy thì SKIP.

    503 busy là phản hồi đúng spec (Q-04) khi nhà cung cấp LLM lỗi — không phải
    lỗi của hệ thống, nên không đánh fail smoke test.
    """
    last = None
    for _ in range(3):
        resp = _ask(client, auth, question, conversation_id)
        if resp.status_code != 503:
            return resp
        last = resp
        time.sleep(5)
    body = last.get_json() or {}
    if body.get("error", {}).get("message") == SERVICE_BUSY_MESSAGE:
        pytest.skip("LLM upstream (OpenRouter free) đang bận — bỏ qua smoke")
    return last


def test_e2e_hoi_dap_tron_luong(e2e_client):
    client, auth = e2e_client
    resp = _ask_with_tolerance(client, auth, "Học phí một tín chỉ là bao nhiêu tiền?")
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body["answer"].strip()
    assert body["mode"] in {"Vector", "Graph", "Hybrid", "None"}
    assert body["conversation_id"]
    assert isinstance(body["sources"], list)
    assert len(body["sources"]) == len(set(body["sources"]))  # không trùng nguồn
    cid = body["conversation_id"]

    # lượt hai cùng conversation: id giữ nguyên, lịch sử đủ 4 lượt
    resp2 = _ask_with_tolerance(
        client, auth, "Vậy điều kiện miễn giảm thì sao?", conversation_id=cid
    )
    assert resp2.status_code == 200, resp2.get_json()
    assert resp2.get_json()["conversation_id"] == cid

    hist = client.get(f"/chat/history?conversation_id={cid}", headers=auth)
    assert hist.status_code == 200
    turns = hist.get_json()["turns"]
    assert len(turns) == 4
    assert [t["role"] for t in turns] == ["user", "assistant", "user", "assistant"]

    # user khác không xem được
    from src.platform.security.auth import issue_token

    other = client.get(
        f"/chat/history?conversation_id={cid}",
        headers={"Authorization": f"Bearer {issue_token('e2e-user-khac')}"},
    )
    assert other.status_code == 200
    assert other.get_json()["turns"] == []
