import pytest
import requests

from src.modules.chat.domain.prompt import SERVICE_BUSY_MESSAGE
from src.modules.chat.infrastructure import retry as retry_mod
from src.shared.common.errors import ExternalServiceError


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


@pytest.fixture()
def sleep_spy(monkeypatch):
    calls: list[float] = []
    monkeypatch.setattr(retry_mod.time, "sleep", lambda s: calls.append(s))
    return calls


@pytest.fixture()
def post_script(monkeypatch):
    """Ghi lại số lần gọi post, trả lời theo kịch bản cho sẵn."""

    def install(script: list):
        state = {"calls": 0}

        def fake_post(url, **kwargs):
            state["calls"] += 1
            item = script[min(state["calls"] - 1, len(script) - 1)]
            if isinstance(item, Exception):
                raise item
            return item

        monkeypatch.setattr(retry_mod.requests, "post", fake_post)
        return state

    return install


def call(max_retries: int = 2, backoff: float = 0.5):
    return retry_mod.post_json_with_retry(
        "https://example.test/v1/chat",
        service="svc",
        headers={},
        payload={},
        timeout=1,
        max_retries=max_retries,
        backoff_seconds=backoff,
    )


def test_thanh_cong_lan_dau_khong_thu_lai(post_script, sleep_spy):
    state = post_script([FakeResponse(200)])
    assert call().status_code == 200
    assert state["calls"] == 1
    assert sleep_spy == []


def test_timeout_roi_thanh_cong_thu_lai_cho_tang_dan(post_script, sleep_spy):
    state = post_script([requests.Timeout("cham"), FakeResponse(200)])
    assert call(max_retries=2, backoff=0.5).status_code == 200
    assert state["calls"] == 2
    assert sleep_spy == [0.5]


def test_http_429_duoc_thu_lai(post_script, sleep_spy):
    state = post_script([FakeResponse(429), FakeResponse(200)])
    assert call().status_code == 200
    assert state["calls"] == 2


def test_http_401_dung_ngay_khong_thu_lai(post_script, sleep_spy):
    state = post_script([FakeResponse(401)])
    with pytest.raises(ExternalServiceError):
        call(max_retries=3)
    assert state["calls"] == 1
    assert sleep_spy == []


def test_http_400_dung_ngay_khong_thu_lai(post_script, sleep_spy):
    state = post_script([FakeResponse(400)])
    with pytest.raises(ExternalServiceError):
        call(max_retries=3)
    assert state["calls"] == 1
    assert sleep_spy == []


def test_het_luot_thu_500_moi_nang_loi(post_script, sleep_spy):
    state = post_script([FakeResponse(500)])
    with pytest.raises(ExternalServiceError):
        call(max_retries=2, backoff=0.5)
    assert state["calls"] == 3  # 1 lần đầu + 2 lần thử lại
    assert sleep_spy == [0.5, 1.0]


def test_loi_ket_noi_het_luot_thu_moi_nang(post_script, sleep_spy):
    state = post_script([requests.ConnectionError("mat ket noi")])
    with pytest.raises(ExternalServiceError):
        call(max_retries=1)
    assert state["calls"] == 2


def test_thong_bao_nguoi_dung_va_ma_503(post_script):
    post_script([FakeResponse(500)])
    with pytest.raises(ExternalServiceError) as exc_info:
        call()
    assert exc_info.value.message == SERVICE_BUSY_MESSAGE
    assert exc_info.value.http_status == 503


def test_http_403_dung_ngay_khong_thu_lai(post_script, sleep_spy):
    state = post_script([FakeResponse(403)])
    with pytest.raises(ExternalServiceError):
        call(max_retries=3)
    assert state["calls"] == 1
    assert sleep_spy == []


def test_loi_ket_noi_roi_thanh_cong_van_thu_lai(post_script, sleep_spy):
    state = post_script([requests.ConnectionError("mat"), FakeResponse(200)])
    assert call(max_retries=2, backoff=0.5).status_code == 200
    assert state["calls"] == 2
    assert sleep_spy == [0.5]


def test_max_retries_0_chi_go_mot_lan(post_script, sleep_spy):
    state = post_script([FakeResponse(500)])
    with pytest.raises(ExternalServiceError):
        call(max_retries=0)
    assert state["calls"] == 1
    assert sleep_spy == []
