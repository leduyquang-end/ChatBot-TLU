from dataclasses import replace

import numpy as np
import pytest

from src.modules.chat.domain.prompt import SERVICE_BUSY_MESSAGE
from src.modules.chat.infrastructure.hf_embedder import SentenceTransformerEmbedder
from src.shared.common.errors import ExternalServiceError
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


class FakeModel:
    def __init__(self, vectors=None) -> None:
        self.calls: list[dict] = []
        self._vectors = vectors

    def encode(self, texts, normalize_embeddings=False):
        self.calls.append(
            {"texts": list(texts), "normalize_embeddings": normalize_embeddings}
        )
        if self._vectors is not None:
            return self._vectors
        return np.array([[0.5, -0.25] for _ in texts])


def make_embedder(model) -> SentenceTransformerEmbedder:
    embedder = SentenceTransformerEmbedder(make_settings())
    embedder._model = model  # type: ignore[assignment]
    return embedder


def test_embed_rong_tra_rong_khong_load_model():
    class NeverLoad(FakeModel):
        def encode(self, *args, **kwargs):
            raise AssertionError("không được gọi encode")

    embedder = make_embedder(NeverLoad())
    assert embedder.embed([]) == []


def test_embed_chuyen_sang_float_va_normalize():
    model = FakeModel(vectors=np.array([[1, 2], [3.5, 4.5]]))
    embedder = make_embedder(model)
    out = embedder.embed(["a", "b"])
    assert out == [[1.0, 2.0], [3.5, 4.5]]
    assert all(type(x) is float for row in out for x in row)
    assert model.calls == [{"texts": ["a", "b"], "normalize_embeddings": True}]


def test_embed_loi_sang_busy_503():
    class BrokenModel:
        def encode(self, texts, normalize_embeddings=False):
            raise RuntimeError("model sập")

    embedder = make_embedder(BrokenModel())
    with pytest.raises(ExternalServiceError) as exc_info:
        embedder.embed(["a"])
    assert exc_info.value.message == SERVICE_BUSY_MESSAGE
    assert exc_info.value.http_status == 503


def _fake_sentence_transformers(monkeypatch):
    import sys
    import types

    created: list = []

    class FakeSentenceTransformer:
        def __init__(self, model_name, token=None):
            self.model_name = model_name
            self.token = token
            self.max_seq_length = None
            created.append(self)

    module = types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer)
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)
    return created


def test_token_mau_trong_env_khong_truyen_cho_model(monkeypatch):
    created = _fake_sentence_transformers(monkeypatch)
    settings = replace(make_settings(), hf_token="your-huggingface-token")
    embedder = SentenceTransformerEmbedder(settings)

    model = embedder._load()

    assert model.token is None
    assert model.max_seq_length == settings.embedding_max_tokens
    assert created == [model]


def test_token_that_duoc_truyen_cho_model(monkeypatch):
    _fake_sentence_transformers(monkeypatch)
    settings = replace(make_settings(), hf_token="hf_real_token")
    embedder = SentenceTransformerEmbedder(settings)

    model = embedder._load()

    assert model.token == "hf_real_token"
