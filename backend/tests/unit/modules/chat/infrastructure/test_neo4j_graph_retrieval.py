import json
from typing import Self

import pytest

from src.modules.chat.infrastructure.neo4j_graph_retrieval import (
    Neo4jGraphRetrieval,
    Neo4jGraphWriter,
)
from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    monkeypatch.setattr("src.modules.chat.infrastructure.retry.time.sleep", lambda s: None)


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
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


class FakeSession:
    def __init__(self, node_records=None, edge_records=None) -> None:
        self._node_records = node_records or []
        self._edge_records = edge_records or []
        self.queries: list[tuple[str, dict]] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args) -> bool:
        return False

    def run(self, cypher: str, **params):
        self.queries.append((cypher, params))
        if "RETURN n.name AS name" in cypher:
            return list(self._node_records)
        return list(self._edge_records)


class FakeDriver:
    def __init__(self, node_records=None, edge_records=None) -> None:
        self._session = FakeSession(node_records, edge_records)

    def session(self) -> FakeSession:
        return self._session


class BrokenDriver:
    def session(self) -> FakeSession:
        session = FakeSession()
        session.run = self._boom  # type: ignore[method-assign]
        return session

    @staticmethod
    def _boom(*args, **kwargs):
        raise RuntimeError("neo4j down")


def make_retrieval(driver, entities=None) -> Neo4jGraphRetrieval:
    retrieval = Neo4jGraphRetrieval(make_settings(), FakeEmbedder(), "key")
    retrieval._load = lambda: driver  # type: ignore[method-assign]
    retrieval._extract_entities = lambda q: list(entities or [])  # type: ignore[method-assign]
    return retrieval


NODES = [
    {
        "name": "Xác suất thống kê",
        "description": "Môn Xác suất thống kê là học phần cơ sở",
        "entity_type": "mon_hoc",
        "embedding": [1.0, 0.0],
    },
    {
        "name": "Học phí",
        "description": "Mức học phí mỗi tín chỉ",
        "entity_type": "chu_de",
        "embedding": [0.0, 1.0],
    },
]

EDGES = [
    {
        "source": "Xác suất thống kê",
        "target": "Xử lý tín hiệu",
        "description": "học trước",
        "confidence": 0.9,
    }
]


def test_retrieve_graph_cham_diem_va_lay_canh():
    driver = FakeDriver(node_records=NODES, edge_records=EDGES)
    retrieval = make_retrieval(driver, entities=["Xác suất thống kê"])
    ctx = retrieval.retrieve("Học phần nào học trước Xác suất thống kê?", alpha=0.5, fetch_k=10)
    assert ctx.mode == "Graph"
    names = [n["name"] for n in ctx.graph.nodes]
    assert names == ["Xác suất thống kê", "Học phí"]
    assert ctx.graph.nodes[0]["score"] == pytest.approx(1.0)
    assert ctx.graph.nodes[1]["score"] == pytest.approx(0.0)
    assert ctx.graph.edges == EDGES
    cypher, params = driver._session.queries[1]
    assert "RETURN a.name AS source" in cypher
    assert params["names"] == ["Xác suất thống kê", "Học phí"]


def test_retrieve_khong_trich_duoc_thuc_te_fallback_ve_tu():
    driver = FakeDriver(node_records=NODES, edge_records=EDGES)
    retrieval = make_retrieval(driver, entities=[])
    ctx = retrieval.retrieve("Điều kiện học bổng năm học 2026?", alpha=0.7, fetch_k=5)
    assert ctx.mode == "Graph"
    assert len(ctx.graph.nodes) == 2
    assert len(driver._session.queries) == 2


def test_retrieve_khong_co_node_khong_query_canh():
    driver = FakeDriver(node_records=[], edge_records=EDGES)
    retrieval = make_retrieval(driver, entities=["khong ton tai"])
    ctx = retrieval.retrieve("Câu hỏi không khớp node nào?", alpha=0.7, fetch_k=5)
    assert ctx.graph.nodes == []
    assert ctx.graph.edges == []
    assert len(driver._session.queries) == 1


def test_loi_neo4j_thanh_ngoai_dich_vu():
    retrieval = make_retrieval(BrokenDriver(), entities=["Xác suất"])
    with pytest.raises(ExternalServiceError) as exc_info:
        retrieval.retrieve("Học phần học trước gì?", alpha=0.7, fetch_k=5)
    assert exc_info.value.message == "Kho quan hệ không truy cập được"


class FakeResponse:
    def __init__(self, *, status_code: int = 200, content: str = "") -> None:
        self.status_code = status_code
        self.text = content
        self._content = content

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self._content}}]}


def _install_post(monkeypatch, *, response=None, exception=None) -> None:
    def fake_post(*args, **kwargs):
        if exception is not None:
            raise exception
        return response

    monkeypatch.setattr(
        "src.modules.chat.infrastructure.retry.requests.post", fake_post
    )


def test_extract_entities_json_hop_le_gioi_han_5(monkeypatch):
    payload = json.dumps({"entities": ["e1", "e2", "e3", "e4", "e5", "e6", "e7"]})
    _install_post(monkeypatch, response=FakeResponse(content=payload))
    retrieval = Neo4jGraphRetrieval(make_settings(), FakeEmbedder(), "key")
    assert retrieval._extract_entities("q") == ["e1", "e2", "e3", "e4", "e5"]


def test_extract_entities_json_sai_tra_ve_rong(monkeypatch):
    _install_post(monkeypatch, response=FakeResponse(content="khong phai json"))
    retrieval = Neo4jGraphRetrieval(make_settings(), FakeEmbedder(), "key")
    assert retrieval._extract_entities("q") == []


def test_extract_entities_groq_loi_tra_ve_rong_de_fallback(monkeypatch):
    _install_post(monkeypatch, response=FakeResponse(status_code=500, content="loi"))
    retrieval = Neo4jGraphRetrieval(make_settings(), FakeEmbedder(), "key")
    assert retrieval._extract_entities("q") == []


def test_extract_entities_401_tra_ve_rong_khong_thu_lai(monkeypatch):
    _install_post(monkeypatch, response=FakeResponse(status_code=401, content="unauth"))
    retrieval = Neo4jGraphRetrieval(make_settings(), FakeEmbedder(), "key")
    assert retrieval._extract_entities("q") == []


def test_extract_entities_entities_khong_phai_list_tra_ve_rong(monkeypatch):
    _install_post(monkeypatch, response=FakeResponse(content='{"entities": "hoc phi"}'))
    retrieval = Neo4jGraphRetrieval(make_settings(), FakeEmbedder(), "key")
    assert retrieval._extract_entities("q") == []


def test_extract_entities_chuyen_kieu_sang_chu(monkeypatch):
    payload = json.dumps({"entities": [2026, "học phí"]})
    _install_post(monkeypatch, response=FakeResponse(content=payload))
    retrieval = Neo4jGraphRetrieval(make_settings(), FakeEmbedder(), "key")
    assert retrieval._extract_entities("q") == ["2026", "học phí"]


def test_extract_entities_thieu_khoa_entities_tra_ve_rong(monkeypatch):
    _install_post(monkeypatch, response=FakeResponse(content="{}"))
    retrieval = Neo4jGraphRetrieval(make_settings(), FakeEmbedder(), "key")
    assert retrieval._extract_entities("q") == []


def test_retrieve_gioi_han_theo_fetch_k():
    records = [
        {
            "name": f"mon {i}",
            "description": "",
            "entity_type": "",
            "embedding": [1.0, 0.0],
        }
        for i in range(15)
    ]
    driver = FakeDriver(node_records=records, edge_records=[])
    retrieval = make_retrieval(driver, entities=["mon"])
    ctx = retrieval.retrieve("q", alpha=0.7, fetch_k=5)
    assert len(ctx.graph.nodes) == 5


def test_retrieve_alpha_thay_doi_thu_hang():
    nodes = [
        {
            "name": "Tin học",
            "description": "máy tính",
            "entity_type": "",
            "embedding": [1.0, 0.0],
        },
        {
            "name": "Môn lạ",
            "description": "là môn xac suat",
            "entity_type": "",
            "embedding": [0.0, 1.0],
        },
    ]
    driver = FakeDriver(node_records=nodes, edge_records=[])

    retrieval = make_retrieval(driver, entities=["xac suat"])
    by_semantic = retrieval.retrieve("q", alpha=1.0, fetch_k=10)
    by_keyword = retrieval.retrieve("q", alpha=0.0, fetch_k=10)

    assert [n["name"] for n in by_semantic.graph.nodes] == ["Tin học", "Môn lạ"]
    assert [n["name"] for n in by_keyword.graph.nodes] == ["Môn lạ", "Tin học"]


def test_retrieve_node_thieu_embedding_van_cham_duoc_keyword():
    nodes = [
        {
            "name": "X",
            "description": "là môn xac suat",
            "entity_type": "",
            "embedding": None,
        }
    ]
    driver = FakeDriver(node_records=nodes, edge_records=[])
    retrieval = make_retrieval(driver, entities=["xac suat"])
    ctx = retrieval.retrieve("q", alpha=0.7, fetch_k=5)
    assert ctx.graph.nodes[0]["score"] == pytest.approx(0.3)


def test_retrieve_node_ten_rong_bi_bo_qua():
    records = [
        {"name": "", "description": "rác", "entity_type": "", "embedding": [1.0, 0.0]},
        {"name": "Có tên", "description": "", "entity_type": "", "embedding": [1.0, 0.0]},
    ]
    driver = FakeDriver(node_records=records, edge_records=[])
    retrieval = make_retrieval(driver, entities=[])
    ctx = retrieval.retrieve("q", alpha=0.7, fetch_k=5)
    assert [n["name"] for n in ctx.graph.nodes] == ["Có tên"]


def test_retrieve_loi_dich_vu_ngoai_bi_nang_len():
    retrieval = make_retrieval(FakeDriver(), entities=[])

    def boom(question: str) -> list[str]:
        raise ExternalServiceError("groq down")

    retrieval._extract_entities = boom  # type: ignore[method-assign]
    with pytest.raises(ExternalServiceError) as exc_info:
        retrieval.retrieve("q", alpha=0.7, fetch_k=5)
    assert exc_info.value.message == "groq down"

class RecordingSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args) -> bool:
        return False

    def run(self, cypher: str, **params) -> None:
        self.calls.append((cypher, params))


class RecordingDriver:
    def __init__(self) -> None:
        self._session = RecordingSession()

    def session(self) -> RecordingSession:
        return self._session


def make_writer() -> tuple[Neo4jGraphWriter, RecordingDriver]:
    writer = Neo4jGraphWriter(make_settings())
    driver = RecordingDriver()
    writer._load = lambda: driver  # type: ignore[method-assign]
    return writer, driver


def test_upsert_entity_ghi_embedding_vao_coi():
    writer, driver = make_writer()
    writer.upsert_entity("Học phí", "Mức học phí mỗi tín chỉ", "chu_de", embedding=[0.1, 0.2])
    cypher, params = driver._session.calls[0]
    assert "MERGE (e:Entity {name: $name})" in cypher
    assert "e.embedding = COALESCE($embedding, e.embedding)" in cypher
    assert params["name"] == "Học phí"
    assert params["description"] == "Mức học phí mỗi tín chỉ"
    assert params["entity_type"] == "chu_de"
    assert params["embedding"] == [0.1, 0.2]


def test_upsert_entity_khong_truyen_embedding_van_chay():
    writer, driver = make_writer()
    writer.upsert_entity("Học bổng", "Loại hình học bổng", "chu_de")
    _, params = driver._session.calls[0]
    assert params["embedding"] is None


def test_upsert_relation_ghi_dung_tham_so():
    writer, driver = make_writer()
    writer.upsert_relation("X", "Y", "học trước", 0.9)
    cypher, params = driver._session.calls[0]
    assert "MERGE (a)-[r:RELATES_TO]->(b)" in cypher
    assert params == {
        "source": "X",
        "target": "Y",
        "description": "học trước",
        "confidence": 0.9,
    }


def test_upsert_relation_tu_tro_hoac_rong_khong_ghi():
    writer, driver = make_writer()
    writer.upsert_relation("X", "X", "tự trỏ", 0.9)
    writer.upsert_relation("", "Y", "thiếu nguồn", 0.9)
    writer.upsert_relation("X", "", "thiếu đích", 0.9)
    assert driver._session.calls == []
