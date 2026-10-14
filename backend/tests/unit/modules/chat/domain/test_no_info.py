from src.modules.chat.domain.no_info import NoInfoPolicy
from src.modules.chat.domain.retrieval_result import (
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
