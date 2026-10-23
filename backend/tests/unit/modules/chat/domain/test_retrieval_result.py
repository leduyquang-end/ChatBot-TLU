import pytest

from src.modules.chat.domain.retrieval_result import (
    GraphContext,
    RetrievedChunk,
    RetrievedContext,
)


def test_citation_dung_source_truoc():
    chunk = RetrievedChunk(text="x", score=0.9, source="QĐ-01")
    assert chunk.citation() == "QĐ-01"


def test_citation_fallback_metadata_document():
    chunk = RetrievedChunk(text="x", score=0.9, metadata={"document": "a.pdf"})
    assert chunk.citation() == "a.pdf"


def test_citation_fallback_metadata_sheet():
    chunk = RetrievedChunk(text="x", score=0.9, metadata={"sheet": "MonHoc"})
    assert chunk.citation() == "MonHoc"


def test_citation_rong_khi_khong_co_gi():
    chunk = RetrievedChunk(text="x", score=0.9)
    assert chunk.citation() == ""


def test_graph_context_empty_va_best_score():
    empty = GraphContext()
    assert empty.is_empty()
    assert empty.best_score() == 0.0

    graph = GraphContext(
        nodes=[{"name": "A", "score": 0.3}, {"name": "B", "score": 0.8}]
    )
    assert not graph.is_empty()
    assert graph.best_score() == pytest.approx(0.8)


def test_graph_context_chi_co_canh_van_khong_rong():
    graph = GraphContext(edges=[{"source": "A", "target": "B"}])
    assert not graph.is_empty()
    assert graph.best_score() == 0.0


def test_context_empty_theo_ca_hai_nhannh():
    assert RetrievedContext(mode="Vector").is_empty()
    assert not RetrievedContext(
        mode="Vector", chunks=[RetrievedChunk(text="x", score=0.5)]
    ).is_empty()
    assert not RetrievedContext(
        mode="Graph", graph=GraphContext(nodes=[{"name": "A", "score": 0.1}])
    ).is_empty()


def test_best_score_chon_diem_lon_nhat_trong_ca_chunk_va_graph():
    context = RetrievedContext(
        mode="Hybrid",
        chunks=[RetrievedChunk(text="x", score=0.4)],
        graph=GraphContext(nodes=[{"name": "A", "score": 0.9}]),
    )
    assert context.best_score() == pytest.approx(0.9)

    context_low_graph = RetrievedContext(
        mode="Hybrid",
        chunks=[RetrievedChunk(text="x", score=0.7)],
        graph=GraphContext(nodes=[{"name": "A", "score": 0.2}]),
    )
    assert context_low_graph.best_score() == pytest.approx(0.7)


def test_best_score_rong_bang_khong():
    assert RetrievedContext(mode="None").best_score() == 0.0
