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
