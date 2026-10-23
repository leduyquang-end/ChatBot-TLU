import pytest

from src.modules.chat.domain.retrieval_mode import RetrievalMode
from src.modules.chat.infrastructure.groq_router_client import GroqRouterClient
from src.shared.config.settings import Settings


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    monkeypatch.setattr("src.modules.chat.infrastructure.retry.time.sleep", lambda s: None)


def make_settings() -> Settings:
    return Settings(
        groq_api_key="g",
        qwen_api_key="q",
        hf_token="h",
        chroma_url="http://localhost:8001",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="pw",
    )


class FakeResponse:
    def __init__(self, status_code: int = 200, content: str = "") -> None:
        self.status_code = status_code
        self.text = content
        self._content = content

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self._content}}]}


def _install_post(monkeypatch, *, response=None, exception=None) -> None:
    def fake_post(*args, **kwargs):
        if exception is not None:
            raise exception
        return response

    monkeypatch.setattr(
        "src.modules.chat.infrastructure.retry.requests.post", fake_post
    )


def test_router_json_sai_dinh_dang_ve_vector(monkeypatch):
    _install_post(monkeypatch, response=FakeResponse(content="khong phai json"))
    router = GroqRouterClient(make_settings())
    assert router.classify("Điều kiện học bổng là gì?") == RetrievalMode.VECTOR


def test_router_nhan_la_ve_vector(monkeypatch):
    _install_post(monkeypatch, response=FakeResponse(content='{"mode": "Random"}'))
    router = GroqRouterClient(make_settings())
    assert router.classify("Điều kiện học bổng là gì?") == RetrievalMode.VECTOR


def test_router_http_500_ve_vector(monkeypatch):
    _install_post(monkeypatch, response=FakeResponse(status_code=500, content="loi"))
    router = GroqRouterClient(make_settings())
    assert router.classify("Điều kiện học bổng là gì?") == RetrievalMode.VECTOR


def test_router_timeout_ve_vector(monkeypatch):
    import requests

    _install_post(monkeypatch, exception=requests.Timeout("het thoi gian"))
    router = GroqRouterClient(make_settings())
    assert router.classify("Điều kiện học bổng là gì?") == RetrievalMode.VECTOR


def test_router_hop_le_tra_ve_graph(monkeypatch):
    _install_post(monkeypatch, response=FakeResponse(content='{"mode": "Graph"}'))
    router = GroqRouterClient(make_settings())
    assert router.classify("Học phần nào học trước môn X?") == RetrievalMode.GRAPH


def test_router_phan_hoi_thieu_choices_ve_vector(monkeypatch):
    class NoChoicesResponse:
        status_code = 200
        text = ""

        def json(self) -> dict:
            return {"id": "chatcmpl-x"}

    _install_post(monkeypatch, response=NoChoicesResponse())
    router = GroqRouterClient(make_settings())
    assert router.classify("Điều kiện học bổng là gì?") == RetrievalMode.VECTOR
