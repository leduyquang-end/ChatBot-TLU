from __future__ import annotations

import logging

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
            import os

            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self._settings.embedding_model,
                token=os.environ.get("HF_TOKEN") or None,
            )
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            model = self._load()
            vectors = model.encode(texts, normalize_embeddings=True)
            return [list(map(float, v)) for v in vectors]
        except Exception as exc:
            logger.error("event=chat.embed.error reason=%s", type(exc).__name__)
            raise ExternalServiceError("Không nhúng được văn bản") from exc
