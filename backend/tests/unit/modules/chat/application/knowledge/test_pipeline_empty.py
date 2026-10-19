from pathlib import Path

from src.modules.chat.application.knowledge.pipeline import KnowledgeIngestPipeline


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
        settings, vector_store=FakeStore(), graph_writer=FakeWriter(), embedder=FakeEmbedder()
    )
    report = pipeline.run(tmp_path)
    assert report.chunk_count == 0
    assert report.documents_failed == []
