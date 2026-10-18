from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import requests

from src.modules.chat.application.knowledge.dedup import merge_entities
from src.modules.chat.application.knowledge.loaders import load_document
from src.shared.config.settings import Settings

logger = logging.getLogger(__name__)

ENTITY_TYPES = [
    "MonHoc",
    "NganhHoc",
    "HocPhi",
    "HocBong",
    "HocKy",
    "BoMon",
    "DoiTuong",
    "ThuTuc",
]

EXTRACT_SYSTEM = """BÃ¡ÂºÂ¡n lÃƒÂ  trÃ¡Â»Â£ lÃƒÂ½ trÃƒÂ­ch xuÃ¡ÂºÂ¥t tri thÃ¡Â»Â©c tÃ¡Â»Â« tÃƒÂ i liÃ¡Â»â€¡u cÃ¡Â»Â§a TrÃ†Â°Ã¡Â»Âng Ã„ÂÃ¡ÂºÂ¡i hÃ¡Â»Âc ThÃ¡Â»Â§y LÃ¡Â»Â£i.
TrÃƒÂ­ch thÃ¡Â»Â±c thÃ¡Â»Æ’ vÃƒÂ  quan hÃ¡Â»â€¡ tÃ¡Â»Â« Ã„â€˜oÃ¡ÂºÂ¡n vÃ„Æ’n bÃ¡ÂºÂ£n.
CÃƒÂ¡c loÃ¡ÂºÂ¡i thÃ¡Â»Â±c thÃ¡Â»Æ’: {types}.
Quy tÃ¡ÂºÂ¯c:
- ChÃ¡Â»â€° trÃƒÂ­ch thÃƒÂ´ng tin cÃƒÂ³ trong vÃ„Æ’n bÃ¡ÂºÂ£n, khÃƒÂ´ng suy Ã„â€˜oÃƒÂ¡n.
- MÃ¡Â»â€”i thÃ¡Â»Â±c thÃ¡Â»Æ’ cÃƒÂ³ name, description, entity_type.
- MÃ¡Â»â€”i quan hÃ¡Â»â€¡ cÃƒÂ³ source, target, description, confidence (0 Ã„â€˜Ã¡ÂºÂ¿n 1).
TrÃ¡ÂºÂ£ vÃ¡Â»Â JSON: {{"entities": [...], "relations": [...]}}"""


@dataclass
class IngestReport:
    documents_ok: list[str] = field(default_factory=list)
    documents_failed: list[str] = field(default_factory=list)
    chunk_count: int = 0
    entity_count: int = 0
    relation_count: int = 0
    merge_count: int = 0

    def to_dict(self) -> dict:
        return {
            "documents_ok": self.documents_ok,
            "documents_failed": self.documents_failed,
            "chunk_count": self.chunk_count,
            "entity_count": self.entity_count,
            "relation_count": self.relation_count,
            "merge_count": self.merge_count,
        }


class KnowledgeIngestPipeline:
    """QT-02: nÃ¡ÂºÂ¡p tri thÃ¡Â»Â©c vÃƒÂ o ChromaDB vÃƒÂ  Neo4j."""

    def __init__(
        self,
        settings: Settings,
        *,
        vector_store,
        graph_writer,
        embedder,
    ) -> None:
        self._settings = settings
        self._vector_store = vector_store
        self._graph_writer = graph_writer
        self._embedder = embedder

    def run(self, source_dir: Path) -> IngestReport:
        report = IngestReport()
        all_chunks: list[dict] = []
        all_entities: list[dict] = []

        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.name.startswith("~$"):
                continue
            try:
                chunks = load_document(path)
                all_chunks.extend(chunks)
                report.documents_ok.append(path.name)
                logger.info(
                    "event=ingest.document.done file=%s chunks=%d", path.name, len(chunks)
                )
            except Exception as exc:  # noqa: BLE001
                report.documents_failed.append(path.name)
                logger.error(
                    "event=ingest.document.error file=%s reason=%s",
                    path.name,
                    type(exc).__name__,
                )

        # NhÃƒÂ¡nh vector
        if all_chunks:
            self._vector_store.add_chunks(all_chunks)
            report.chunk_count = len(all_chunks)

        # NhÃƒÂ¡nh Ã„â€˜Ã¡Â»â€œ thÃ¡Â»â€¹: trÃƒÂ­ch thÃ¡Â»Â±c thÃ¡Â»Æ’ bÃ¡ÂºÂ±ng Qwen
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file() or path.name not in report.documents_ok:
                continue
            try:
                chunks = load_document(path)
            except Exception:  # noqa: BLE001, S112
                continue
            for chunk in chunks:
                entities, relations = self._extract_entities(chunk["text"])
                for ent in entities:
                    ent.setdefault("relations", [])
                for rel in relations:
                    src = rel.get("source", "")
                    for ent in entities:
                        if ent.get("name") == src:
                            ent["relations"].append(rel)
                all_entities.extend(entities)

        embeddings = None
        if all_entities:
            names_and_desc = [
                f"{e.get('name', '')} {e.get('description', '')}" for e in all_entities
            ]
            try:
                embeddings = self._embedder.embed(names_and_desc)
            except Exception:  # noqa: BLE001
                embeddings = None

        merged, merge_count = merge_entities(
            all_entities,
            threshold=self._settings.dedup_threshold,
            embeddings=embeddings,
        )
        report.merge_count = merge_count
        report.entity_count = len(merged)

        relation_total = 0
        for ent in merged:
            emb = None
            try:
                emb = self._embedder.embed(
                    [f"{ent.get('name', '')} {ent.get('description', '')}"]
                )[0]
            except Exception:  # noqa: BLE001
                emb = None
            self._graph_writer.upsert_entity(
                name=ent.get("name", ""),
                description=ent.get("description", ""),
                entity_type=ent.get("entity_type", ""),
                embedding=emb,
            )
            for rel in ent.get("relations", []):
                self._graph_writer.upsert_relation(
                    source=rel.get("source", ent.get("name", "")),
                    target=rel.get("target", ""),
                    description=rel.get("description", ""),
                    confidence=float(rel.get("confidence", 0.0)),
                )
                relation_total += 1
        report.relation_count = relation_total

        logger.info("event=ingest.batch.done %s", json.dumps(report.to_dict(), ensure_ascii=False))
        return report

    def _extract_entities(self, text: str) -> tuple[list[dict], list[dict]]:
        prompt = EXTRACT_SYSTEM.format(types=", ".join(ENTITY_TYPES)) + f"\n\nÃ„ÂoÃ¡ÂºÂ¡n vÃ„Æ’n bÃ¡ÂºÂ£n:\n{text[:4000]}"
        try:
            response = requests.post(
                "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._settings.qwen_api_key}"},
                json={
                    "model": self._settings.answer_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                },
                timeout=self._settings.request_timeout_seconds,
            )
            if response.status_code >= 400:
                logger.warning("event=ingest.extract.error status=%d", response.status_code)
                return [], []
            content = response.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            entities = data.get("entities", []) or []
            relations = data.get("relations", []) or []
            # Validate loÃ¡ÂºÂ¡i thÃ¡Â»Â±c thÃ¡Â»Æ’
            valid_entities = [
                e
                for e in entities
                if e.get("entity_type") in ENTITY_TYPES and e.get("name")
            ]
            return valid_entities, relations
        except Exception as exc:  # noqa: BLE001
            logger.warning("event=ingest.extract.error reason=%s", type(exc).__name__)
            return [], []
