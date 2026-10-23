import pytest

from src.modules.chat.domain.graph_scoring import (
    cosine_similarity,
    entity_embedding_text,
    keyword_ratio,
    rank_entities,
    score_entity,
)


def test_cosine_hai_vector_giong_nhau_la_1():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)


def test_cosine_vuong_goc_la_0():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_hai_chieu_duong():
    assert cosine_similarity([1.0, 1.0], [1.0, 0.0]) == pytest.approx(2**0.5 / 2)


def test_cosine_vec_rong_lech_chieu_hoac_toan_zero_la_0():
    assert cosine_similarity([], [1.0]) == 0.0
    assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0


def test_keyword_ratio_khop_day_du():
    assert keyword_ratio("Học phí", "áp dụng theo học kỳ", ["học phí"]) == 1.0


def test_keyword_ratio_khop_mot_phan():
    assert keyword_ratio("Học phí", "áp dụng theo học kỳ", ["học phí", "học bổng"]) == 0.5


def test_keyword_ratio_khong_khoap_va_khong_co_tu_khoa_la_0():
    assert keyword_ratio("Điều 1", "nội dung", ["học bổng"]) == 0.0
    assert keyword_ratio("Điều 1", "nội dung", []) == 0.0


def test_score_entity_theo_alpha_la_cong_thuc_adr06():
    node = {"name": "Môn học", "description": "", "embedding": [1.0, 0.0]}
    query = [1.0, 0.0]  # semantic = 1, keyword = 0 (từ khóa không khớp)
    keywords = ["học bổng"]
    assert score_entity(node, query, keywords, alpha=1.0) == pytest.approx(1.0)
    assert score_entity(node, query, keywords, alpha=0.0) == pytest.approx(0.0)
    assert score_entity(node, query, keywords, alpha=0.7) == pytest.approx(0.7)


def test_score_entity_thieu_embedding_chi_cong_diem_keyword():
    node = {"name": "Học phí", "description": "", "embedding": None}
    score = score_entity(node, [1.0, 0.0], ["học phí", "học bổng"], alpha=0.7)
    assert score == pytest.approx(0.3 * 0.5)


def test_score_entity_semantic_am_duoc_cat_ve_0():
    node = {"name": "X", "description": "", "embedding": [1.0, 0.0]}
    query = [-1.0, 0.0]  # cosine = -1
    assert score_entity(node, query, [], alpha=0.7) == pytest.approx(0.0)


def test_rank_entities_xep_giam_dan_theo_diem():
    nodes = [
        # semantic=1, keyword=0 → 0.7
        {"name": "Không khớp", "description": "", "embedding": [1.0, 0.0]},
        # semantic=1, keyword=1 → 1.0
        {"name": "Học phí", "description": "", "embedding": [1.0, 0.0]},
        # semantic=0.6, keyword=0 → 0.42
        {"name": "Trùng khớp yếu", "description": "", "embedding": [0.6, 0.8]},
    ]
    ranked = rank_entities(nodes, [1.0, 0.0], ["học phí"], alpha=0.7, limit=3)
    assert [n["name"] for n in ranked] == ["Học phí", "Không khớp", "Trùng khớp yếu"]
    assert ranked[0]["score"] >= ranked[1]["score"] >= ranked[2]["score"]


def test_rank_entities_gioi_han_va_bo_node_khong_co_ten():
    nodes = [
        {"name": "", "description": "bỏ qua", "embedding": None},
        {"name": "A", "description": "", "embedding": [1.0]},
        {"name": "B", "description": "", "embedding": [1.0]},
    ]
    ranked = rank_entities(nodes, [1.0], [], alpha=0.7, limit=1)
    assert len(ranked) == 1
    assert ranked[0]["name"] in {"A", "B"}


def test_rank_entities_limit_am_tra_ve_rong():
    assert rank_entities([{"name": "A"}], [1.0], [], alpha=0.7, limit=0) == []


def test_entity_embedding_text_dung_dinh_dang_nap():
    assert entity_embedding_text("Học phí", "1.000.000đ") == "Học phí 1.000.000đ"
