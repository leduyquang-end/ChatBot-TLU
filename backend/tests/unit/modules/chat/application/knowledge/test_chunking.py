import pytest

from src.modules.chat.application.knowledge.chunking import chunk_text


def test_van_ban_rong_tra_danh_sach_rong():
    assert chunk_text("   \n  ") == []


def test_chunk_size_am_nem_value_error():
    with pytest.raises(ValueError):
        chunk_text("nội dung", chunk_size=0)


def test_overlap_lon_hon_chunk_nem_value_error():
    with pytest.raises(ValueError):
        chunk_text("nội dung đủ dài", chunk_size=10, overlap=10)


def test_cat_theo_dieu_va_giu_section():
    text = "Mở đầu\n\nĐiều 1. Quy định chung\n" + "A" * 50 + "\n\nĐiều 2. Học phí\n" + "B" * 50
    chunks = chunk_text(text, chunk_size=800)
    texts = [c["text"] for c in chunks]
    assert any(t.startswith("Điều 1") for t in texts)
    assert any(t.startswith("Điều 2") for t in texts)
    assert all("section" in c["metadata"] for c in chunks)


def test_do_dai_va_metadata_khi_vuot_chunk_size():
    text = ("Nội dung điều khoản khá dài và lặp lại. " * 40).strip()
    chunks = chunk_text(text, chunk_size=100, overlap=20, metadata={"document": "QD.pdf"})
    assert len(chunks) > 3
    assert all(len(c["text"]) <= 100 for c in chunks)
    assert all(c["metadata"]["document"] == "QD.pdf" for c in chunks)
    assert all(c["metadata"]["section"] for c in chunks)
