from src.modules.chat.application.knowledge.table_processing import (
    drop_total_and_note_rows,
    fill_merged_cells,
    rows_to_blocks,
)


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
