from src.modules.chat.domain.retrieval_mode import RetrievalMode


def test_ac03_router_sai_dinh_dang_ve_vector():
    assert RetrievalMode.from_label("sai dinh dang") == RetrievalMode.VECTOR
    assert RetrievalMode.from_label("") == RetrievalMode.VECTOR
    assert RetrievalMode.from_label("Unknown") == RetrievalMode.VECTOR


def test_router_nhan_dung():
    assert RetrievalMode.from_label("vector") == RetrievalMode.VECTOR
    assert RetrievalMode.from_label("Graph") == RetrievalMode.GRAPH
    assert RetrievalMode.from_label("Hybrid") == RetrievalMode.HYBRID
    assert RetrievalMode.from_label("None") == RetrievalMode.NONE


def test_from_label_none_va_khoang_trang():
    assert RetrievalMode.from_label(None) == RetrievalMode.VECTOR  # type: ignore[arg-type]
    assert RetrievalMode.from_label("   ") == RetrievalMode.VECTOR
    assert RetrievalMode.from_label("  Graph  ") == RetrievalMode.GRAPH


def test_from_label_khong_phan_biet_hoa_thuong():
    assert RetrievalMode.from_label("GRAPH") == RetrievalMode.GRAPH
    assert RetrievalMode.from_label("hYbRiD") == RetrievalMode.HYBRID
    assert RetrievalMode.from_label("nOnE") == RetrievalMode.NONE
