import json
from pathlib import Path

from src.modules.chat.application.knowledge.pipeline import KnowledgeIngestPipeline
from src.shared.config.settings import Settings
from src.shared.events import EventBus, KnowledgeIngested


def make_settings(**overrides) -> Settings:
    base = {
        "groq_api_key": "g",
        "qwen_api_key": "q",
        "hf_token": "h",
        "chroma_url": "http://localhost:8001",
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "pw",
    }
    base.update(overrides)
    return Settings(**base)


class FakeStore:
    def __init__(self) -> None:
        self.batches: list[list[dict]] = []

    def add_chunks(self, chunks) -> None:
        self.batches.append(list(chunks))


class FakeWriter:
    def __init__(self) -> None:
        self.entities: list[dict] = []
        self.relations: list[dict] = []

    def upsert_entity(self, **kwargs) -> None:
        self.entities.append(kwargs)

    def upsert_relation(self, **kwargs) -> None:
        self.relations.append(kwargs)


class FakeEmbedder:
    def embed(self, texts):
        return [[0.5, 0.5] for _ in texts]


class BoomEmbedder:
    def embed(self, texts):
        raise RuntimeError("hf sập")


def make_pipeline(tmp_path: Path, settings=None, *, extract=None):
    store = FakeStore()
    writer = FakeWriter()
    pipeline = KnowledgeIngestPipeline(
        settings or make_settings(),
        vector_store=store,
        graph_writer=writer,
        embedder=FakeEmbedder(),
        event_bus=EventBus(),
    )
    if extract is not None:
        pipeline._extract_entities = extract  # type: ignore[method-assign]
    return pipeline, store, writer


CHUNKS = [
    {"text": "Điều 1. Học phí được quy định rõ.", "metadata": {"document": "qd.txt"}}
]
ENTS = [
    {"name": "Học phí", "description": "Mức học phí mỗi tín chỉ", "entity_type": "HocPhi"}
]
RELS = [
    {
        "source": "Học phí",
        "target": "Sinh viên",
        "description": "áp dụng",
        "confidence": 0.8,
    }
]


def fake_extract_ok(text: str):
    # copy sâu — pipeline mutate ent["relations"] khi gắn quan hệ
    return json.loads(json.dumps(ENTS)), json.loads(json.dumps(RELS)), {
        "status": "ok",
        "model": "moc",
    }


def test_run_nap_vector_va_do_thi_day_du(tmp_path: Path, monkeypatch):
    (tmp_path / "qd.txt").write_text("nội dung", encoding="utf-8")
    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.load_document",
        lambda path: list(CHUNKS),
    )
    pipeline, store, writer = make_pipeline(tmp_path, extract=fake_extract_ok)
    report = pipeline.run(tmp_path)

    assert report.documents_ok == ["qd.txt"]
    assert report.documents_failed == []
    assert report.chunk_count == len(CHUNKS)
    assert store.batches == [CHUNKS]
    assert report.entity_count == 1
    assert report.relation_count == 1
    assert report.merge_count == 0

    assert writer.entities[0]["name"] == "Học phí"
    assert writer.entities[0]["entity_type"] == "HocPhi"
    assert writer.entities[0]["embedding"] == [0.5, 0.5]
    assert writer.relations == [
        {
            "source": "Học phí",
            "target": "Sinh viên",
            "description": "áp dụng",
            "confidence": 0.8,
        }
    ]

    log = tmp_path / "processed" / "extract_log.jsonl"
    assert log.exists()
    entry = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    assert entry["file"] == "qd.txt"
    assert entry["status"] == "ok"
    assert entry["model"] == "moc"
    assert len(entry["entities"]) == 1


def test_run_resume_bo_qua_file_da_trich_ok(tmp_path: Path, monkeypatch):
    (tmp_path / "qd.txt").write_text("nội dung", encoding="utf-8")
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "extract_log.jsonl").write_text(
        json.dumps({"file": "qd.txt", "status": "ok"}) + "\n", encoding="utf-8"
    )

    def must_not_run(text: str):
        raise AssertionError("không được trích lại file đã xong")

    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.load_document",
        lambda path: list(CHUNKS),
    )
    pipeline, store, writer = make_pipeline(tmp_path, extract=must_not_run)
    report = pipeline.run(tmp_path)

    assert report.documents_ok == ["qd.txt"]
    assert store.batches == [CHUNKS]
    assert writer.entities == []


def test_run_file_loi_vao_documents_failed_khong_ngung(tmp_path: Path, monkeypatch):
    (tmp_path / "hua.txt").write_text("nội dung", encoding="utf-8")

    def boom(path):
        raise ValueError("file hỏng")

    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.load_document", boom
    )
    pipeline, store, writer = make_pipeline(tmp_path, extract=fake_extract_ok)
    report = pipeline.run(tmp_path)

    assert report.documents_failed == ["hua.txt"]
    assert report.documents_ok == []
    assert store.batches == []
    assert writer.entities == []


def test_run_bo_chu_trung_va_quan_he_tu_tro(tmp_path: Path, monkeypatch):
    (tmp_path / "qd.txt").write_text("nội dung", encoding="utf-8")
    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.load_document",
        lambda path: list(CHUNKS),
    )

    def extract(text: str):
        return (
            [
                {
                    "name": "Khoa Công nghệ thông tin",
                    "description": "khoa đại học负责 quản lý",
                    "entity_type": "BoMon",
                }
            ],
            [
                {
                    "source": "Khoa Công nghệ thông tin",
                    "target": "Khoa Công nghệ thông tin",
                    "description": "tự trỏ",
                    "confidence": 0.9,
                },
                {
                    "source": "Khoa Công nghệ thông tin",
                    "target": "Sinh viên",
                    "description": "负责 quản lý",
                    "confidence": 0.8,
                },
            ],
            {"status": "ok", "model": "moc"},
        )

    pipeline, _store, writer = make_pipeline(tmp_path, extract=extract)
    report = pipeline.run(tmp_path)

    assert writer.entities[0]["description"] == "khoa đại học quản lý"
    assert [r["target"] for r in writer.relations] == ["Sinh viên"]
    assert writer.relations[0]["description"] == "quản lý"
    assert report.relation_count == 1


def test_run_embedder_loi_van_upsert_embedding_none(tmp_path: Path, monkeypatch):
    (tmp_path / "qd.txt").write_text("nội dung", encoding="utf-8")
    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.load_document",
        lambda path: list(CHUNKS),
    )
    pipeline, _store, writer = make_pipeline(tmp_path, extract=fake_extract_ok)
    pipeline._embedder = BoomEmbedder()  # type: ignore[assignment]
    report = pipeline.run(tmp_path)

    assert report.entity_count == 1
    assert writer.entities[0]["embedding"] is None
    assert len(writer.relations) == 1


def test_extract_key_placeholder_bo_quang_ma_khong_go_api():
    pipeline = KnowledgeIngestPipeline(
        make_settings(qwen_api_key="your-key"),
        vector_store=FakeStore(),
        graph_writer=FakeWriter(),
        embedder=FakeEmbedder(),
        event_bus=EventBus(),
    )
    entities, relations, meta = pipeline._extract_entities("text")
    assert entities == []
    assert relations == []
    assert meta["status"] == "skipped"


class FakeResp:
    def __init__(self, status_code: int = 200, content: str = "") -> None:
        self.status_code = status_code
        self.text = content
        self._content = content

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self._content}}]}


def make_extract_pipeline(**settings_overrides):
    return KnowledgeIngestPipeline(
        make_settings(**settings_overrides),
        vector_store=FakeStore(),
        graph_writer=FakeWriter(),
        embedder=FakeEmbedder(),
        event_bus=EventBus(),
    )


def test_extract_json_hop_le_va_loc_entity_type(monkeypatch):
    payload = json.dumps(
        {
            "entities": [
                {"name": "Học phí", "description": "d", "entity_type": "HocPhi"},
                {"name": "Loại sai", "description": "d", "entity_type": "SaiLoai"},
                {"description": "thiếu tên", "entity_type": "MonHoc"},
            ],
            "relations": [{"source": "a", "target": "b", "confidence": 0.5}],
        }
    )
    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.requests.post",
        lambda *a, **k: FakeResp(content=payload),
    )
    pipeline = make_extract_pipeline(answer_model="moc")
    entities, relations, meta = pipeline._extract_entities("đoạn văn")
    assert [e["name"] for e in entities] == ["Học phí"]
    assert len(relations) == 1
    assert meta == {"status": "ok", "model": "moc"}


def test_extract_json_fence_md_van_doc_duoc(monkeypatch):
    payload = json.dumps({"entities": [], "relations": []})
    fenced = f"```json\n{payload}\n```"
    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.requests.post",
        lambda *a, **k: FakeResp(content=fenced),
    )
    pipeline = make_extract_pipeline(answer_model="moc")
    entities, _relations, meta = pipeline._extract_entities("đoạn văn")
    assert meta["status"] == "ok"
    assert entities == []


def test_extract_http_400_sang_model_ke(monkeypatch):
    payload = json.dumps(
        {"entities": [{"name": "X", "description": "d", "entity_type": "MonHoc"}]}
    )
    responses = [FakeResp(status_code=400, content="bad"), FakeResp(content=payload)]
    calls = []

    def fake_post(*args, **kwargs):
        calls.append(kwargs)
        return responses[len(calls) - 1]

    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.requests.post", fake_post
    )
    pipeline = make_extract_pipeline(answer_model="m1, m2")
    entities, _, meta = pipeline._extract_entities("đoạn văn")
    assert len(calls) == 2
    assert meta == {"status": "ok", "model": "m2"}
    assert len(entities) == 1


def test_extract_429_thu_lai_thanh_cong(monkeypatch):
    payload = json.dumps(
        {"entities": [{"name": "X", "description": "d", "entity_type": "MonHoc"}]}
    )
    responses = [FakeResp(status_code=429, content="rate"), FakeResp(content=payload)]
    calls = []
    sleeps = []

    def fake_post(*args, **kwargs):
        calls.append(kwargs)
        return responses[len(calls) - 1]

    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.requests.post", fake_post
    )
    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.time.sleep",
        lambda s: sleeps.append(s),
    )
    pipeline = make_extract_pipeline(answer_model="moc")
    _, _, meta = pipeline._extract_entities("đoạn văn")
    assert len(calls) == 2
    assert sleeps == [1]
    assert meta["status"] == "ok"


def test_extract_json_sai_tra_status_error(monkeypatch):
    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.requests.post",
        lambda *a, **k: FakeResp(content="không phải json"),
    )
    pipeline = make_extract_pipeline(answer_model="moc")
    entities, relations, meta = pipeline._extract_entities("đoạn văn")
    assert entities == []
    assert relations == []
    assert meta["status"] == "error"
    assert meta["model"] is None




def test_pipeline_chay_khong_co_file(tmp_path: Path):
    class FakeStore:
        def add_chunks(self, chunks):
            raise AssertionError("không nên được gọi")

    class FakeWriter:
        def upsert_entity(self, **kwargs):
            raise AssertionError("không nên được gọi")

        def upsert_relation(self, **kwargs):
            raise AssertionError("không nên được gọi")

    class FakeEmbedder:
        def embed(self, texts):
            return [[0.0] for _ in texts]

    from src.shared.config.settings import Settings

    settings = Settings(
        groq_api_key="g",
        qwen_api_key="q",
        hf_token="h",
        chroma_url="http://localhost:8000",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="pw",
    )
    pipeline = KnowledgeIngestPipeline(
        settings,
        vector_store=FakeStore(),
        graph_writer=FakeWriter(),
        embedder=FakeEmbedder(),
        event_bus=EventBus(),
    )
    report = pipeline.run(tmp_path)
    assert report.chunk_count == 0
    assert report.documents_failed == []


def test_run_phat_su_kien_knowledge_ingested(tmp_path: Path, monkeypatch):
    (tmp_path / "qd.txt").write_text("nội dung", encoding="utf-8")
    monkeypatch.setattr(
        "src.modules.chat.application.knowledge.pipeline.load_document",
        lambda path: list(CHUNKS),
    )

    bus = EventBus()
    received: list[KnowledgeIngested] = []
    bus.subscribe(KnowledgeIngested, received.append)
    pipeline = KnowledgeIngestPipeline(
        make_settings(qwen_api_key="your-key"),
        vector_store=FakeStore(),
        graph_writer=FakeWriter(),
        embedder=FakeEmbedder(),
        event_bus=bus,
    )

    report = pipeline.run(tmp_path)

    assert len(received) == 1
    event = received[0]
    assert event.chunks == report.chunk_count
    assert event.entities == report.entity_count
    assert event.relations == report.relation_count
    assert event.duration_seconds >= 0
