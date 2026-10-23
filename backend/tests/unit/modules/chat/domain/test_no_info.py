from src.modules.chat.domain.no_info import NoInfoPolicy
from src.modules.chat.domain.retrieval_result import (
    GraphContext,
    RetrievedChunk,
    RetrievedContext,
)


def test_ac02_khong_co_thong_tin_khi_rong():
    policy = NoInfoPolicy(threshold=0.15)
    context = RetrievedContext(mode="Vector")
    assert not policy.has_relevant_info(context)


def test_ac02_khong_co_thong_tin_khi_diem_thap():
    policy = NoInfoPolicy(threshold=0.5)
    context = RetrievedContext(
        mode="Vector",
        chunks=[RetrievedChunk(text="abc", score=0.1)],
    )
    assert not policy.has_relevant_info(context)


def test_co_thong_tin_khi_diem_cao():
    policy = NoInfoPolicy(threshold=0.15)
    context = RetrievedContext(
        mode="Vector",
        chunks=[RetrievedChunk(text="abc", score=0.8)],
    )
    assert policy.has_relevant_info(context)


def test_graph_node_diem_cao_la_co_thong_tin():
    policy = NoInfoPolicy(threshold=0.15)
    context = RetrievedContext(
        mode="Graph",
        graph=GraphContext(nodes=[{"name": "Học phí", "score": 0.9}]),
    )
    assert policy.has_relevant_info(context)


def test_graph_node_diem_duoi_nguong_la_khong_co_thong_tin():
    policy = NoInfoPolicy(threshold=0.15)
    context = RetrievedContext(
        mode="Graph",
        graph=GraphContext(nodes=[{"name": "Rác", "score": 0.05}]),
    )
    assert not policy.has_relevant_info(context)


def test_graph_rong_khong_co_thong_tin():
    policy = NoInfoPolicy(threshold=0.15)
    context = RetrievedContext(mode="Graph")
    assert not policy.has_relevant_info(context)
