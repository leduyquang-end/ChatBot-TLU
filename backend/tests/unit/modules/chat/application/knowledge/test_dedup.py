from src.modules.chat.application.knowledge.dedup import merge_entities


def test_gop_theo_cosine_du_nguong():
    entities = [
        {"name": "Miễn giảm học phí", "description": "A", "entity_type": "HocPhi", "relations": []},
        {"name": "Chính sách miễn giảm", "description": "B", "entity_type": "HocPhi", "relations": []},
    ]
    embeddings = [[1.0, 0.0], [0.99, 0.05]]
    merged, count = merge_entities(entities, threshold=0.92, embeddings=embeddings)
    assert count == 1
    assert len(merged) == 1


def test_cosine_duoi_nguong_khong_gop():
    entities = [
        {"name": "A", "description": "x", "entity_type": "HocPhi", "relations": []},
        {"name": "B", "description": "y", "entity_type": "HocPhi", "relations": []},
    ]
    embeddings = [[1.0, 0.0], [0.0, 1.0]]
    merged, count = merge_entities(entities, threshold=0.92, embeddings=embeddings)
    assert count == 0
    assert len(merged) == 2


def test_so_luong_embedding_lech_bo_qua_giai_doan_hai():
    entities = [
        {"name": "A", "description": "x", "entity_type": "HocPhi", "relations": []},
        {"name": "B", "description": "y", "entity_type": "HocPhi", "relations": []},
    ]
    merged, count = merge_entities(entities, threshold=0.92, embeddings=[[1.0, 0.0]])
    assert count == 0
    assert len(merged) == 2


def test_ten_rong_bi_bo_qua():
    entities = [
        {"name": "  ", "description": "rác", "entity_type": "HocPhi", "relations": []},
        {"name": "Học phí", "description": "hợp lệ", "entity_type": "HocPhi", "relations": []},
    ]
    merged, _ = merge_entities(entities)
    assert [e["name"] for e in merged] == ["Học phí"]


def test_quan_he_trung_giu_confidence_cao_hon():
    entities = [
        {
            "name": "Học phí",
            "description": "một",
            "entity_type": "HocPhi",
            "relations": [
                {"source": "Học phí", "target": "X", "description": "thấp", "confidence": 0.4}
            ],
        },
        {
            "name": "Học phí",
            "description": "hai",
            "entity_type": "HocPhi",
            "relations": [
                {"source": "Học phí", "target": "X", "description": "cao", "confidence": 0.9}
            ],
        },
    ]
    merged, count = merge_entities(entities)
    assert count == 1
    assert len(merged[0]["relations"]) == 1
    assert merged[0]["relations"][0]["confidence"] == 0.9


def test_gop_ten_chi_khac_hoa_thuong():
    """'Học kỳ' và 'học kỳ' là cùng một thực thể — không tạo 2 node trùng."""
    entities = [
        {"name": "Học kỳ", "description": "ngắn", "entity_type": "HocKy", "relations": []},
        {
            "name": "học kỳ",
            "description": "mô tả dài hơn nhiều",
            "entity_type": "HocKy",
            "relations": [],
        },
    ]
    merged, count = merge_entities(entities)
    assert count == 1
    assert len(merged) == 1
    assert merged[0]["name"] == "Học kỳ"
    assert merged[0]["description"] == "mô tả dài hơn nhiều"
