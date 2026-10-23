from src.modules.chat.domain.retrieval_result import RetrievedChunk
from src.modules.chat.infrastructure.chroma_retrieval import ChromaVectorRetrieval
from src.shared.config.settings import Settings


def make_settings() -> Settings:
    return Settings(
        groq_api_key="g",
        qwen_api_key="q",
        hf_token="h",
        chroma_url="http://localhost:8001",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="pw",
    )


class FakeEmbedder:
    def __init__(self, vector: list[float]) -> None:
        self._vector = vector

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(self._vector) for _ in texts]


class FakeCollection:
    def __init__(self, results: dict) -> None:
        self._results = results
        self.calls: list[dict] = []

    def query(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return self._results


def make_retrieval(results: dict) -> tuple[ChromaVectorRetrieval, FakeCollection]:
    retrieval = ChromaVectorRetrieval(make_settings(), FakeEmbedder([1.0, 0.0]))
    collection = FakeCollection(results)
    retrieval._collection = collection
    return retrieval, collection


def test_diem_la_cosine_thu_thuc_tu_embedding():
    results = {
        "documents": [["giong hoi", "thuan goc", "nguoc goc"]],
        "metadatas": [[{"document": "a.pdf"}, {"document": "b.pdf"}, {"document": "c.pdf"}]],
        "distances": [[0.5, 1.5, 0.1]],
        "embeddings": [[[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]]],
    }
    retrieval, collection = make_retrieval(results)
    ctx = retrieval.retrieve("hoi", fetch_k=3, top_k=3)
    assert [round(c.score, 4) for c in ctx.chunks] == [1.0, 0.0, 0.0]
    assert "embeddings" in collection.calls[0]["include"]


def test_thieu_embedding_fallback_theo_dist():
    results = {
        "documents": [["mot", "hai"]],
        "metadatas": [[{"document": "a.pdf"}, {"document": "b.pdf"}]],
        "distances": [[0.5, 1.5]],
    }
    retrieval, _ = make_retrieval(results)
    ctx = retrieval.retrieve("hoi", fetch_k=2, top_k=2)
    assert [round(c.score, 4) for c in ctx.chunks] == [0.5, 0.0]


def test_embedding_dang_numpy_van_cham_diem():
    import numpy as np

    results = {
        "documents": [["giong hoi", "thuan goc"]],
        "metadatas": [[{"document": "a.pdf"}, {"document": "b.pdf"}]],
        "distances": [[0.5, 1.5]],
        "embeddings": np.array([[[1.0, 0.0], [0.0, 1.0]]]),
    }
    retrieval, _ = make_retrieval(results)
    ctx = retrieval.retrieve("hoi", fetch_k=2, top_k=2)
    assert [round(c.score, 4) for c in ctx.chunks] == [1.0, 0.0]


def test_ket_qua_rong_tra_chunks_rong():
    retrieval, _ = make_retrieval({})
    ctx = retrieval.retrieve("hoi", fetch_k=5, top_k=5)
    assert ctx.chunks == []
    assert ctx.mode == "Vector"


def test_mmr_chon_doan_khac_nhau_thay_vi_giong_nhau():
    retrieval, _ = make_retrieval({})
    candidates = [
        RetrievedChunk(text="học phí tín chỉ đại học", score=0.9),
        RetrievedChunk(text="học phí tín chỉ đại học mới", score=0.89),
        RetrievedChunk(text="quy chế đào tạo luận văn", score=0.8),
    ]
    selected = retrieval._mmr([1.0, 0.0], candidates, top_k=2)
    texts = [c.text for c in selected]
    assert texts[0] == "học phí tín chỉ đại học"
    # bản giống hệt bị phạt diversity → lấy đoạn khác (điểm thấp hơn nhưng đa dạng)
    assert texts[1] == "quy chế đào tạo luận văn"


def test_mmr_it_hon_top_k_tra_toan_bo():
    retrieval, _ = make_retrieval({})
    candidates = [RetrievedChunk(text="a", score=0.9), RetrievedChunk(text="b", score=0.8)]
    assert len(retrieval._mmr([1.0], candidates, top_k=5)) == 2
    assert retrieval._mmr([1.0], [], top_k=5) == []


def test_mmr_so_luong_dung_top_k():
    retrieval, _ = make_retrieval({})
    candidates = [
        RetrievedChunk(text=f"đoạn {i} nội dung khác nhau hẳn", score=0.9 - i * 0.01)
        for i in range(6)
    ]
    selected = retrieval._mmr([1.0, 0.0], candidates, top_k=3)
    assert len(selected) == 3
    assert len({c.text for c in selected}) == 3


def test_text_similarity_trong_hop_phan_ra_khac():
    same = ChromaVectorRetrieval._text_similarity("học phí one", "học phí two")
    assert 0.0 < same < 1.0
    assert ChromaVectorRetrieval._text_similarity("học phí", "luận văn") == 0.0
    assert ChromaVectorRetrieval._text_similarity("", "abc") == 0.0
    assert ChromaVectorRetrieval._text_similarity("a b c", "a b c") == 1.0
