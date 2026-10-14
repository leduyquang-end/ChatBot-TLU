from src.modules.chat.domain.prompt import (
    NO_INFO_MESSAGE,
    ROLE_PROMPT,
    build_prompt,
)
from src.modules.chat.domain.retrieval_result import RetrievedChunk, RetrievedContext


def test_prompt_co_du_5_phan():
    context = RetrievedContext(
        mode="Vector",
        chunks=[RetrievedChunk(text="Nội dung điều 1", score=0.9, source="QĐ-01")],
    )
    prompt = build_prompt(
        "Học phí bao nhiêu?", context, [{"role": "user", "content": "Xin chào"}]
    )
    assert ROLE_PROMPT in prompt
    assert "Quy tắc" in prompt
    assert "Lịch sử hội thoại" in prompt
    assert "Tài liệu" in prompt
    assert "Câu hỏi hiện tại" in prompt
    assert "Học phí bao nhiêu?" in prompt
    assert "QĐ-01" in prompt


def test_no_info_message_la_thong_bao_co_dinh():
    assert "chưa có thông tin" in NO_INFO_MESSAGE
    assert "liên hệ" in NO_INFO_MESSAGE


def test_prompt_mode_none_khong_co_tai_lieu():
    context = RetrievedContext(mode="None")
    prompt = build_prompt("Xin chào", context, [])
    assert "không truy xuất" in prompt
