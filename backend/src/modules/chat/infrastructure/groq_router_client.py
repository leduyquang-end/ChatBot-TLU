from __future__ import annotations

import logging

import requests

from src.modules.chat.domain.retrieval_mode import RetrievalMode
from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """Bạn là bộ chọn cách tìm thông tin cho chatbot Trường Đại học Thủy Lợi.
Trả về CHỈ một object JSON dạng {"mode": "<nhãn>"}, trong đó nhãn là một trong:
- "Vector": định nghĩa, quy định chi tiết
- "Graph": quan hệ, điều kiện tiên quyết, liên kết giữa các mục
- "Hybrid": câu hỏi phức tạp, cần suy luận nhiều bước
- "None": lời chào, giao tiếp thông thường
Không giải thích. Không viết thêm gì khác ngoài JSON."""

FEW_SHOT = [
    ("Xin chào", '{"mode": "None"}'),
    ("Điều kiện xét học bổng là gì?", '{"mode": "Vector"}'),
    ("Học phần nào phải học trước môn X?", '{"mode": "Graph"}'),
    (
        "Sinh viên ngành X học lại môn nào thì được miễn học phí?",
        '{"mode": "Hybrid"}',
    ),
]


class GroqRouterClient:
    """Router dùng Llama-3.3-70B qua Groq (ADR-02). Lỗi → Vector (ADR-08)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def classify(self, question: str) -> RetrievalMode:
        try:
            label = self._call_groq(question)
            return RetrievalMode.from_label(label)
        except Exception as exc:
            logger.warning("event=chat.router.fallback reason=%s", type(exc).__name__)
            return RetrievalMode.VECTOR

    def _call_groq(self, question: str) -> str:
        import json

        messages = [{"role": "system", "content": ROUTER_SYSTEM_PROMPT}]
        for q, a in FEW_SHOT:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": a})
        messages.append({"role": "user", "content": question})

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._settings.groq_api_key}"},
            json={
                "model": self._settings.router_model,
                "messages": messages,
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
            timeout=self._settings.request_timeout_seconds,
        )
        if response.status_code >= 400:
            raise ExternalServiceError(
                f"Groq lỗi HTTP {response.status_code}",
                detail=response.text[:200],
            )
        content = response.json()["choices"][0]["message"]["content"]
        try:
            data = json.loads(content)
            return str(data.get("mode", "Vector"))
        except json.JSONDecodeError:
            return "Vector"
