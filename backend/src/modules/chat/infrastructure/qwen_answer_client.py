from __future__ import annotations

import logging

import requests

from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings

logger = logging.getLogger(__name__)


class QwenAnswerClient:
    """Sinh câu trả lời bằng Qwen3-235B-A22B (ADR-03)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self._settings.qwen_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._settings.qwen_api_key}"},
                json={
                    "model": self._settings.answer_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
                timeout=self._settings.request_timeout_seconds,
            )
            if response.status_code >= 400:
                raise ExternalServiceError(
                    f"Qwen lỗi HTTP {response.status_code}",
                    detail=response.text[:200],
                )
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.RequestException as exc:
            logger.error("event=chat.answer.error service=qwen reason=%s", type(exc).__name__)
            raise ExternalServiceError("Dịch vụ sinh câu trả lời không phản hồi") from exc
