import pytest
import requests

from src.modules.chat.domain.prompt import SERVICE_BUSY_MESSAGE
from src.modules.chat.infrastructure.qwen_answer_client import QwenAnswerClient
from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    monkeypatch.setattr("src.modules.chat.infrastructure.retry.time.sleep", lambda s: None)


def make_settings(**overrides) -> Settings:
    return Settings(
        groq_api_key="g",
        qwen_api_key="q",
        hf_token="h",
        chroma_url="http://localhost:8001",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="pw",
        **overrides,
    )


class FakeResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


class JsonResponse:
    def __init__(self, data: dict) -> None:
        self.status_code = 200
        self.text = ""
        self._data = data

    def json(self) -> dict:
        return self._data


def _install_post(monkeypatch, *, response=None, exception=None) -> None:
    def fake_post(*args, **kwargs):
        if exception is not None:
            raise exception
        return response

    monkeypatch.setattr(
        "src.modules.chat.infrastructure.retry.requests.post", fake_post
    )


def test_qwen_loi_http_tra_thong_bao_tam_thoi(monkeypatch):
    _install_post(monkeypatch, response=FakeResponse(500, "loi server"))
    client = QwenAnswerClient(make_settings())
    with pytest.raises(ExternalServiceError) as exc_info:
        client.generate("prompt")
    assert exc_info.value.message == SERVICE_BUSY_MESSAGE


def test_qwen_timeout_tra_thong_bao_tam_thoi(monkeypatch):
    _install_post(monkeypatch, exception=requests.Timeout("het thoi gian"))
    client = QwenAnswerClient(make_settings())
    with pytest.raises(ExternalServiceError) as exc_info:
        client.generate("prompt")
    assert exc_info.value.message == SERVICE_BUSY_MESSAGE


def test_qwen_ma_loi_van_la_503(monkeypatch):
    _install_post(monkeypatch, response=FakeResponse(503, "dang tai"))
    client = QwenAnswerClient(make_settings())
    with pytest.raises(ExternalServiceError) as exc_info:
        client.generate("prompt")
    assert exc_info.value.http_status == 503


def test_qwen_phan_hoi_thieu_choices_sang_busy(monkeypatch):
    _install_post(monkeypatch, response=JsonResponse({"error": "sai dinh dang"}))
    client = QwenAnswerClient(make_settings())
    with pytest.raises(ExternalServiceError) as exc_info:
        client.generate("prompt")
    assert exc_info.value.message == SERVICE_BUSY_MESSAGE


def test_qwen_content_null_sang_busy(monkeypatch):
    _install_post(
        monkeypatch,
        response=JsonResponse({"choices": [{"message": {"content": None}}]}),
    )
    client = QwenAnswerClient(make_settings())
    with pytest.raises(ExternalServiceError) as exc_info:
        client.generate("prompt")
    assert exc_info.value.message == SERVICE_BUSY_MESSAGE


@pytest.mark.parametrize("content", ["", "   ", "\n\t "])
def test_qwen_content_rong_sang_busy(monkeypatch, content):
    _install_post(
        monkeypatch,
        response=JsonResponse({"choices": [{"message": {"content": content}}]}),
    )
    client = QwenAnswerClient(make_settings())
    with pytest.raises(ExternalServiceError) as exc_info:
        client.generate("prompt")
    assert exc_info.value.message == SERVICE_BUSY_MESSAGE


def test_qwen_model_dau_hong_thu_model_ke(monkeypatch):
    settings = make_settings(answer_model="m-broken,m-good")
    calls: list[str] = []
    responses = iter(
        [
            JsonResponse({"error": "thieu choices"}),
            JsonResponse({"choices": [{"message": {"content": "tra loi tot"}}]}),
        ]
    )

    def fake_post(url, *, headers, json, **kwargs):
        calls.append(json["model"])
        return next(responses)

    monkeypatch.setattr(
        "src.modules.chat.infrastructure.retry.requests.post", fake_post
    )
    client = QwenAnswerClient(settings)
    assert client.generate("prompt") == "tra loi tot"
    assert calls == ["m-broken", "m-good"]


def test_qwen_tat_ca_model_deu_hong_moi_busy(monkeypatch):
    settings = make_settings(answer_model="m1,m2")
    calls: list[str] = []

    def fake_post(url, *, headers, json, **kwargs):
        calls.append(json["model"])
        return JsonResponse({"error": "sai dinh dang"})

    monkeypatch.setattr(
        "src.modules.chat.infrastructure.retry.requests.post", fake_post
    )
    client = QwenAnswerClient(settings)
    with pytest.raises(ExternalServiceError) as exc_info:
        client.generate("prompt")
    assert exc_info.value.message == SERVICE_BUSY_MESSAGE
    assert calls == ["m1", "m2"]


def test_qwen_loi_http_khong_thu_model_ke(monkeypatch):
    """500 hết retry: dừng luôn, không đốt latency cho model khác."""
    settings = make_settings(answer_model="m1,m2")
    calls: list[str] = []

    def fake_post(url, *, headers, json, **kwargs):
        calls.append(json["model"])
        return FakeResponse(500, "loi server")

    monkeypatch.setattr(
        "src.modules.chat.infrastructure.retry.requests.post", fake_post
    )
    client = QwenAnswerClient(settings)
    with pytest.raises(ExternalServiceError):
        client.generate("prompt")
    # retry nội bộ nhưng chỉ model m1, không bao giờ tới m2
    assert calls and set(calls) == {"m1"}


def test_qwen_429_het_quota_thu_model_ke(monkeypatch):
    """429 là quota riêng của model → retry hết rồi rơi sang model kế."""
    settings = make_settings(answer_model="m1,m2")
    calls: list[str] = []
    responses = iter(
        [FakeResponse(429, "rate limit")]
        * 4  # m1: 1 + 3 retry
        + [JsonResponse({"choices": [{"message": {"content": "tra loi m2"}}]})]
    )

    def fake_post(url, *, headers, json, **kwargs):
        calls.append(json["model"])
        return next(responses)

    monkeypatch.setattr(
        "src.modules.chat.infrastructure.retry.requests.post", fake_post
    )
    client = QwenAnswerClient(settings)
    assert client.generate("prompt") == "tra loi m2"
    assert calls[-1] == "m2"
    assert set(calls) == {"m1", "m2"}


def test_qwen_401_khong_thu_model_ke(monkeypatch):
    """401 là lỗi chung của key/base_url → model nào cũng vậy, dừng ngay."""
    settings = make_settings(answer_model="m1,m2")
    calls: list[str] = []

    def fake_post(url, *, headers, json, **kwargs):
        calls.append(json["model"])
        return FakeResponse(401, "unauthorized")

    monkeypatch.setattr(
        "src.modules.chat.infrastructure.retry.requests.post", fake_post
    )
    client = QwenAnswerClient(settings)
    with pytest.raises(ExternalServiceError):
        client.generate("prompt")
    assert calls and set(calls) == {"m1"}
