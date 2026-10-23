from src.modules.chat.domain.prompt import (
    NO_INFO_MESSAGE,
    ROLE_PROMPT,
    build_prompt,
)
from src.modules.chat.domain.retrieval_result import (
    GraphContext,
    RetrievedChunk,
    RetrievedContext,
)


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


def test_prompt_co_phan_thuc_the_va_quan_he():
    context = RetrievedContext(
        mode="Graph",
        graph=GraphContext(
            nodes=[{"name": "Học phí", "description": "Mức học phí", "entity_type": "chu_de"}],
            edges=[{"source": "Học phí", "target": "Sinh viên", "description": "ảnh hưởng"}],
        ),
    )
    prompt = build_prompt("Học phí?", context, [])
    assert "[Thực thể 1] (chu_de) Học phí: Mức học phí" in prompt
    assert "[Quan hệ 1] Học phí → Sinh viên: ảnh hưởng" in prompt


def test_prompt_quan_he_thieu_description_dung_type():
    context = RetrievedContext(
        mode="Graph",
        graph=GraphContext(
            edges=[{"source": "A", "target": "B", "type": "RELATES_TO"}],
        ),
    )
    prompt = build_prompt("q", context, [])
    assert "[Quan hệ 1] A → B: RELATES_TO" in prompt


def test_prompt_context_rong_hien_khong_co():
    context = RetrievedContext(mode="Vector")
    prompt = build_prompt("q", context, [])
    assert "(không có)" in prompt


def test_prompt_doan_khong_co_source_dung_ten_tai_lieu_chung():
    context = RetrievedContext(
        mode="Vector",
        chunks=[RetrievedChunk(text="Nội dung", score=0.9)],
    )
    prompt = build_prompt("q", context, [])
    assert "Nguồn: tài liệu" in prompt


def test_format_history_thieu_khoa_van_chay():
    from src.modules.chat.domain.prompt import format_history

    out = format_history([{"role": "user"}, {"content": "lệch"}])
    assert out == "user: \n: lệch"


def test_format_history_nhieu_lieu_tach_dong():
    from src.modules.chat.domain.prompt import format_history

    out = format_history(
        [
            {"role": "user", "content": "câu 1"},
            {"role": "assistant", "content": "trả lời 1"},
            {"role": "user", "content": "câu 2"},
        ]
    )
    assert out.splitlines() == [
        "user: câu 1",
        "assistant: trả lời 1",
        "user: câu 2",
    ]
