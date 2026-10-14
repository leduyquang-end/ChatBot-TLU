from __future__ import annotations

from src.modules.chat.domain.retrieval_result import RetrievedContext


class NoInfoPolicy:
    """ADR-09 / ADR-10: quyết định "không có thông tin".

    Ngưỡng là đề xuất (A-03), đọc từ cấu hình. Khi truy xuất rỗng
    hoặc điểm tốt nhất dưới ngưỡng, trả False.
    """

    def __init__(self, threshold: float) -> None:
        self._threshold = threshold

    def has_relevant_info(self, context: RetrievedContext) -> bool:
        if context.is_empty():
            return False
        return context.best_score() >= self._threshold
