from __future__ import annotations

from typing import Protocol

from src.modules.chat.domain.retrieval_mode import RetrievalMode


class RouterPort(Protocol):
    def classify(self, question: str) -> RetrievalMode:
        """Luôn trả về một trong bốn nhãn. Lỗi → Vector."""
        ...
