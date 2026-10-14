from src.modules.chat.application.knowledge.chunking import chunk_text
from src.modules.chat.application.knowledge.cleaning import clean_text
from src.modules.chat.application.knowledge.dedup import merge_entities
from src.modules.chat.application.knowledge.table_processing import (
    drop_total_and_note_rows,
    fill_merged_cells,
    rows_to_blocks,
)


def test_clean_text_bo_khoang_trang_thua():
    assert clean_text("a   b\n\n\n\nc") == "a b\n\nc"


def test_ac01_chunk_co_metadata():
    text = "Điều 1. Quy định chung.\n" + "Nội dung điều 1. " * 50
    chunks = chunk_text(text, chunk_size=200, overlap=20, metadata={"document": "QD.pdf"})
    assert chunks
    assert all(c["metadata"]["document"] == "QD.pdf" for c in chunks)
    assert all(c["text"] for c in chunks)


def test_ac02_xlsx_dien_om_gop_va_bo_dong_tong():
    rows = [
        ["Mã", "Tên", "Học kỳ"],
        ["MH01", "Lập trình", None],
        [None, None, None],
        ["", "Tổng cộng", ""],
    ]
    filled = fill_merged_cells(rows)
    assert filled[1][2] == "Học kỳ"
    cleaned = drop_total_and_note_rows(filled)
    joined = " ".join(" ".join(str(c or "") for c in r) for r in cleaned).lower()
    assert "tổng cộng" not in joined


def test_ac02_gop_theo_ma_dinh_danh():
    rows = [
        ["Mã", "Tên"],
        ["MH01", "Lập trình"],
        ["MH01", "Python"],
        ["MH02", "Cơ sở dữ liệu"],
    ]
    blocks = rows_to_blocks(rows, sheet="MonHoc")
    assert len(blocks) == 2
    assert "MH01" in blocks[0]["text"]
    assert "Lập trình" in blocks[0]["text"]
    assert "Python" in blocks[0]["text"]


def test_ac03_gop_thuc_the_trung_ten():
    entities = [
        {"name": "Học phí", "description": "Ngắn", "entity_type": "HocPhi", "relations": []},
        {"name": "Học phí", "description": "Mô tả dài hơn về học phí", "entity_type": "HocPhi", "relations": [
            {"source": "Học phí", "target": "Ngành CNTT", "description": "áp dụng", "confidence": 0.9}
        ]},
    ]
    merged, count = merge_entities(entities)
    assert count == 1
    assert len(merged) == 1
    assert merged[0]["description"] == "Mô tả dài hơn về học phí"
    assert len(merged[0]["relations"]) == 1


def test_ac05_merge_idempotent():
    entities = [{"name": "HocBong", "description": "x", "entity_type": "HocBong", "relations": []}]
    merged1, c1 = merge_entities(entities)
    merged2, c2 = merge_entities(merged1)
    assert c1 == 0
    assert c2 == 0
    assert len(merged2) == 1
