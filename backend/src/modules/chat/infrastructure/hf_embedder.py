from __future__ import annotations

import logging

from src.modules.chat.domain.prompt import SERVICE_BUSY_MESSAGE
from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder:
    """Nhúng bằng vietnamese-bi-encoder (ADR-04), 768 chiều."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(
                self._settings.embedding_model,
                token=self._hf_token(),
            )
            model.max_seq_length = self._settings.embedding_max_tokens
            self._model = model
        return self._model

    def _hf_token(self) -> str | None:
        """Token thật mới truyền; giá trị mẫu trong .env.example (your-...) coi như không có.

        Token mẫu gửi lên Hugging Face sẽ bị 401 dù model công khai.
        """
        token = (self._settings.hf_token or "").strip()
        if not token or token.lower().startswith("your-"):
            return None
        return token

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            model = self._load()
            vectors = model.encode(texts, normalize_embeddings=True)
            return [list(map(float, v)) for v in vectors]
        except Exception as exc:
            logger.error("event=chat.embed.error reason=%s", type(exc).__name__)
            raise ExternalServiceError(
                SERVICE_BUSY_MESSAGE, detail=f"Embed lỗi: {type(exc).__name__}: {exc}"
            ) from exc
