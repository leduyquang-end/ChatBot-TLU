from __future__ import annotations

import hashlib
import logging

from src.modules.chat.domain.retrieval_result import RetrievedChunk, RetrievedContext
from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings

logger = logging.getLogger(__name__)


class ChromaVectorRetrieval:
    """Truy xuất vector qua ChromaDB: fetch_k ứng viên, MMR top_k (ADR-05)."""

    def __init__(self, settings: Settings, embedder) -> None:
        self._settings = settings
        self._embedder = embedder
        self._client = None
        self._collection = None

    def _load(self):
        if self._collection is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            client = chromadb.HttpClient(
                host=self._host(),
                port=self._port(),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._client = client
            self._collection = client.get_or_create_collection(
                self._settings.chroma_collection
            )
        return self._collection

    def _host(self) -> str:
        from urllib.parse import urlparse

        parsed = urlparse(self._settings.chroma_url)
        return parsed.hostname or "localhost"

    def _port(self) -> int:
        from urllib.parse import urlparse

        parsed = urlparse(self._settings.chroma_url)
        return parsed.port or 8000

    def add_chunks(self, chunks: list[dict]) -> None:
        """Ghi đoạn với ID ổn định từ nội dung, tránh trùng khi chạy lại."""
        collection = self._load()
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        texts = [c["text"] for c in chunks]
        vectors = self._embedder.embed(texts)
        for chunk, vector in zip(chunks, vectors):
            chunk_id = hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest()
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append(chunk.get("metadata", {}))
            embeddings.append(vector)
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def retrieve(self, question: str, *, fetch_k: int, top_k: int) -> RetrievedContext:
        try:
            collection = self._load()
            query_vec = self._embedder.embed([question])[0]
            results = collection.query(
                query_embeddings=[query_vec],
                n_results=fetch_k,
                include=["documents", "metadatas", "distances"],
            )
            candidates = self._to_chunks(results)
            selected = self._mmr(query_vec, candidates, top_k)
            return RetrievedContext(mode="Vector", chunks=selected)
        except ExternalServiceError:
            raise
        except Exception as exc:
            logger.error("event=chat.retrieval.vector.error reason=%s", type(exc).__name__)
            raise ExternalServiceError("Kho tài liệu không truy cập được") from exc

    def _to_chunks(self, results) -> list[RetrievedChunk]:
        chunks: list[RetrievedChunk] = []
        if not results or not results.get("documents"):
            return chunks
        docs = results["documents"][0] or []
        metas = results["metadatas"][0] or []
        dists = results["distances"][0] or []
        for doc, meta, dist in zip(docs, metas, dists):
            score = 1.0 - float(dist)
            source = (meta or {}).get("document", "") or (meta or {}).get("sheet", "")
            chunks.append(
                RetrievedChunk(text=doc or "", score=score, source=source, metadata=meta or {})
            )
        return chunks

    def _mmr(
        self,
        query_vec: list[float],
        candidates: list[RetrievedChunk],
        top_k: int,
        lambda_: float = 0.5,
    ) -> list[RetrievedChunk]:
        """MMR đơn giản dựa trên cosine đã có trong score + đa dạng theo text."""
        if len(candidates) <= top_k:
            return candidates
        selected: list[RetrievedChunk] = []
        remaining = list(candidates)
        while remaining and len(selected) < top_k:
            best = None
            best_val = float("-inf")
            for cand in remaining:
                relevance = cand.score
                diversity = 0.0
                for sel in selected:
                    diversity = max(diversity, self._text_similarity(cand.text, sel.text))
                mmr_val = lambda_ * relevance - (1 - lambda_) * diversity
                if mmr_val > best_val:
                    best_val = mmr_val
                    best = cand
            if best is None:
                break
            selected.append(best)
            remaining.remove(best)
        return selected

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)
