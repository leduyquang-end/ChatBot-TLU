from __future__ import annotations

import logging

from src.modules.chat.domain.prompt import SERVICE_BUSY_MESSAGE
from src.modules.chat.infrastructure.retry import post_json_with_retry
from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings

logger = logging.getLogger(__name__)

# Lỗi chỉ gắn với đúng model (hết quota 429, model sai 400/404/422) → đáng
# thử model kế. Timeout/5xx/auth là lỗi hệ thống → dừng ngay, không đốt latency.
_MODEL_SPECIFIC_SUFFIXES = ("HTTP 400", "HTTP 404", "HTTP 422", "http_429")


def _is_model_specific_error(detail: str) -> bool:
    return any(detail.endswith(suffix) for suffix in _MODEL_SPECIFIC_SUFFIXES)


class QwenAnswerClient:
    """Sinh câu trả lời bằng Qwen3-235B-A22B (ADR-03).

    `answer_model` có thể là danh sách cách nhau dấu phẩy (OpenRouter fallback):
    model hỏng/thiếu nội dung thì thử model kế, hết danh sách mới trả busy.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate(self, prompt: str) -> str:
        models = [
            m.strip()
            for m in self._settings.answer_model.split(",")
            if m.strip()
        ] or [self._settings.answer_model]
        last_reason = "no_model"
        for model in models:
            try:
                content = self._generate_one(prompt, model)
            except ExternalServiceError as exc:
                if not _is_model_specific_error(exc.detail or ""):
                    # lỗi hệ thống/xác thực/timeout: dừng ngay như cũ
                    raise
                last_reason = exc.detail or "model_error"
                logger.warning(
                    "event=chat.answer.model_fallback service=qwen model=%s detail=%s",
                    model,
                    exc.detail,
                )
                continue
            if content is not None:
                return content
            last_reason = "malformed"
        logger.error(
            "event=chat.answer.failed service=qwen models=%s reason=%s",
            len(models),
            last_reason,
        )
        raise ExternalServiceError(
            SERVICE_BUSY_MESSAGE, detail=f"qwen: {last_reason}"
        )

    def _generate_one(self, prompt: str, model: str) -> str | None:
        """Gọi một model. Trả None nếu response hỏng/thiếu nội dung."""
        try:
            response = post_json_with_retry(
                f"{self._settings.qwen_base_url}/chat/completions",
                service="qwen",
                headers={"Authorization": f"Bearer {self._settings.qwen_api_key}"},
                payload={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
                timeout=self._settings.request_timeout_seconds,
                max_retries=self._settings.max_retries,
                backoff_seconds=self._settings.retry_backoff_seconds,
            )
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (AttributeError, KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning(
                "event=chat.answer.malformed service=qwen model=%s reason=%s",
                model,
                type(exc).__name__,
            )
            return None
        if not isinstance(content, str) or not content.strip():
            logger.warning(
                "event=chat.answer.malformed service=qwen model=%s reason=empty_content",
                model,
            )
            return None
        return content.strip()
