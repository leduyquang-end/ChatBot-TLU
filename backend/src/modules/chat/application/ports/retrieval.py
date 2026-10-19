from __future__ import annotations

from typing import Protocol

from src.modules.chat.domain.retrieval_result import RetrievedContext


class VectorRetrievalPort(Protocol):
    def retrieve(self, question: str, *, fetch_k: int, top_k: int) -> RetrievedContext: ...


class GraphRetrievalPort(Protocol):
    def retrieve(self, question: str, *, alpha: float, fetch_k: int) -> RetrievedContext: ...
