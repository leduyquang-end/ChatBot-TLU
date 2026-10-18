from __future__ import annotations

import logging

import requests

from src.modules.chat.domain.retrieval_mode import RetrievalMode
from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """Báº¡n lÃ  bá»™ chá»n cÃ¡ch tÃ¬m thÃ´ng tin cho chatbot TrÆ°á»ng Äáº¡i há»c Thá»§y Lá»£i.
Tráº£ vá» CHá»ˆ má»™t object JSON dáº¡ng {"mode": "<nhÃ£n>"}, trong Ä‘Ã³ nhÃ£n lÃ  má»™t trong:
- "Vector": Ä‘á»‹nh nghÄ©a, quy Ä‘á»‹nh chi tiáº¿t
- "Graph": quan há»‡, Ä‘iá»u kiá»‡n tiÃªn quyáº¿t, liÃªn káº¿t giá»¯a cÃ¡c má»¥c
- "Hybrid": cÃ¢u há»i phá»©c táº¡p, cáº§n suy luáº­n nhiá»u bÆ°á»›c
- "None": lá»i chÃ o, giao tiáº¿p thÃ´ng thÆ°á»ng
KhÃ´ng giáº£i thÃ­ch. KhÃ´ng viáº¿t thÃªm gÃ¬ khÃ¡c ngoÃ i JSON."""

FEW_SHOT = [
    ("Xin chÃ o", '{"mode": "None"}'),
    ("Äiá»u kiá»‡n xÃ©t há»c bá»•ng lÃ  gÃ¬?", '{"mode": "Vector"}'),
    ("Há»c pháº§n nÃ o pháº£i há»c trÆ°á»›c mÃ´n X?", '{"mode": "Graph"}'),
    (
        "Sinh viÃªn ngÃ nh X há»c láº¡i mÃ´n nÃ o thÃ¬ Ä‘Æ°á»£c miá»…n há»c phÃ­?",
        '{"mode": "Hybrid"}',
    ),
]


class GroqRouterClient:
    """Router dÃ¹ng Llama-3.3-70B qua Groq (ADR-02). Lá»—i â†’ Vector (ADR-08)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def classify(self, question: str) -> RetrievalMode:
        try:
            label = self._call_groq(question)
            return RetrievalMode.from_label(label)
        except Exception as exc:  # noqa: BLE001
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
                f"Groq lá»—i HTTP {response.status_code}",
                detail=response.text[:200],
            )
        content = response.json()["choices"][0]["message"]["content"]
        try:
            data = json.loads(content)
            return str(data.get("mode", "Vector"))
        except json.JSONDecodeError:
            return "Vector"
