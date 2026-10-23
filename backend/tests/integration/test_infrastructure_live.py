from __future__ import annotations

import functools
import math
import socket
from pathlib import Path
from urllib.parse import urlparse

import pytest
from dotenv import load_dotenv

_BACKEND = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND.parent / ".env")

from src.shared.config.settings import get_settings

settings = get_settings()


def _tcp_up(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _skip_unless(up: bool, reason: str) -> None:
    if not up:
        pytest.skip(reason)


@functools.lru_cache(maxsize=1)
def _embedder():
    from src.modules.chat.infrastructure.hf_embedder import SentenceTransformerEmbedder

    embedder = SentenceTransformerEmbedder(settings)
    try:
        embedder.embed(["kiểm tra tải model"])
    except Exception as exc:  # noqa: BLE001 - môi trường thiếu cache thì skip
        pytest.skip(f"không tải được model embed: {exc}")
    return embedder


def _chroma_up() -> bool:
    parsed = urlparse(settings.chroma_url)
    return _tcp_up(parsed.hostname or "localhost", parsed.port or 8000)


def _neo4j_up() -> bool:
    parsed = urlparse(settings.neo4j_uri)
    return _tcp_up(parsed.hostname or "localhost", parsed.port or 7687)


def _groq_up() -> bool:
    return bool(settings.groq_api_key) and _tcp_up("api.groq.com", 443)


def test_embedder_song_tra_768_chieu_chuan_hoa():
    embedder = _embedder()
    try:
        vectors = embedder.embed(["Học phí đại học Thủy Lợi"])
    except Exception as exc:  # noqa: BLE001 - môi trường thiếu model thì skip
        pytest.skip(f"không nhúng được: {exc}")
    vector = vectors[0]
    assert len(vector) == 768
    assert all(type(x) is float for x in vector)
    assert math.isclose(math.sqrt(sum(x * x for x in vector)), 1.0, abs_tol=0.01)


def test_chroma_retrieve_song_diem_trong_khoang_cosine():
    _skip_unless(_chroma_up(), "Chroma không mở")
    from src.modules.chat.infrastructure.chroma_retrieval import ChromaVectorRetrieval

    retrieval = ChromaVectorRetrieval(settings, _embedder())
    ctx = retrieval.retrieve(
        "Học phí một tín chỉ là bao nhiêu?",
        fetch_k=settings.fetch_k,
        top_k=settings.top_k,
    )
    assert ctx.mode == "Vector"
    assert 0 < len(ctx.chunks) <= settings.top_k
    assert all(c.text.strip() for c in ctx.chunks)
    assert all(0.0 <= c.score <= 1.0001 for c in ctx.chunks)


def test_neo4j_score_nodes_song_diem_giam_dan():
    _skip_unless(_neo4j_up(), "Neo4j không mở")
    from src.modules.chat.infrastructure.neo4j_graph_retrieval import (
        Neo4jGraphRetrieval,
    )

    retrieval = Neo4jGraphRetrieval(settings, _embedder(), settings.groq_api_key)
    nodes = retrieval._score_nodes(
        "Học phí", ["học phí"], alpha=1.0, limit=settings.fetch_k
    )
    assert 0 < len(nodes) <= settings.fetch_k
    assert all(n["name"] for n in nodes)
    scores = [n["score"] for n in nodes]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] > 0.2


def test_neo4j_fetch_edges_song_cau_truc_dung():
    _skip_unless(_neo4j_up(), "Neo4j không mở")
    from src.modules.chat.infrastructure.neo4j_graph_retrieval import (
        Neo4jGraphRetrieval,
    )

    retrieval = Neo4jGraphRetrieval(settings, _embedder(), settings.groq_api_key)
    nodes = retrieval._score_nodes(
        "Học phí", ["học phí"], alpha=1.0, limit=settings.fetch_k
    )
    edges = retrieval._fetch_edges([nodes[0]["name"]])
    assert isinstance(edges, list)
    for edge in edges:
        assert edge["source"]
        assert edge["target"]
        assert isinstance(edge["confidence"], float)
        assert edge["confidence"] >= 0.0


def test_router_groq_song_phan_loai_dung_nhan_none():
    _skip_unless(bool(settings.groq_api_key), "thiếu GROQ_API_KEY")
    _skip_unless(_groq_up(), "Không gọi được api.groq.com")
    from src.modules.chat.domain.retrieval_mode import RetrievalMode
    from src.modules.chat.infrastructure.groq_router_client import GroqRouterClient

    router = GroqRouterClient(settings)
    assert router.classify("Xin chào") == RetrievalMode.NONE
    assert router.classify("Điều kiện học bổng là gì?") == RetrievalMode.VECTOR
