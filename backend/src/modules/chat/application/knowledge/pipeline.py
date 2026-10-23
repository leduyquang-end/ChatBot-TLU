from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import requests

from src.modules.chat.application.knowledge.cleaning import strip_cjk
from src.modules.chat.application.knowledge.dedup import merge_entities
from src.modules.chat.application.knowledge.loaders import load_document
from src.modules.chat.domain.graph_scoring import entity_embedding_text
from src.shared.config.settings import Settings
from src.shared.events import EventBus, KnowledgeIngested

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

EXTRACT_SYSTEM = """Bạn là trợ lý trích xuất tri thức từ tài liệu của Trường Đại học Thủy Lợi.
Trích thực thể và quan hệ từ đoạn văn bản.
Các loại thực thể: {types}.
Quy tắc:
- Chỉ trích thông tin có trong văn bản, không suy đoán.
- Mỗi thực thể có name, description, entity_type.
- Mỗi quan hệ có source, target, description, confidence (0 đến 1).
Trả về JSON: {{"entities": [...], "relations": [...]}}"""


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
    """QT-02: nạp tri thức vào ChromaDB và Neo4j."""

    def __init__(
        self,
        settings: Settings,
        *,
        vector_store,
        graph_writer,
        embedder,
        event_bus: EventBus,
    ) -> None:
        self._settings = settings
        self._vector_store = vector_store
        self._graph_writer = graph_writer
        self._embedder = embedder
        self._event_bus = event_bus

    def run(self, source_dir: Path) -> IngestReport:
        started = time.monotonic()
        report = IngestReport()
        all_chunks: list[dict] = []
        chunks_by_file: dict[str, list[dict]] = {}

        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.name.startswith("~$") or path.name.startswith("."):
                continue
            # bỏ thư mục processed/ — nơi dump_knowledge.py ghi báo cáo (output)
            if "processed" in path.parts:
                continue
            try:
                chunks = load_document(path)
                chunks_by_file[path.name] = chunks
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

        # Nhánh vector
        if all_chunks:
            self._vector_store.add_chunks(all_chunks)
            report.chunk_count = len(all_chunks)

        # Nhánh đồ thị: trích + GHI NGAY từng file (đứt giữa chừng không mất),
        # log JSONL tại <source>/processed/extract_log.jsonl để soi lỗi.
        # Resume: file đã trích OK trước đó → bỏ qua, chỉ làm nốt phần dở dang
        done_files: set[str] = set()
        for log_path in sorted(source_dir.rglob("extract_log.jsonl")):
            for line in log_path.read_text(encoding="utf-8").splitlines():
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("status") == "ok" and entry.get("file"):
                    done_files.add(entry["file"])
        todo: list[tuple[str, str]] = []
        for file_name in report.documents_ok:
            if file_name in done_files:
                logger.info(
                    "event=ingest.extract.skip file=%s reason=da_trich_ok",
                    file_name,
                )
                continue
            chunks = chunks_by_file.get(file_name, [])
            sample = "\n".join(c["text"] for c in chunks)[:4000]
            if not sample.strip():
                continue
            todo.append((file_name, sample))

        # LLM là I/O chờ mạng → chạy song song; ghi log/Neo4j tuần tiến ở
        # thread chính nên đứt giữa chừng vẫn không mất file đã xong.
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {
                pool.submit(self._extract_entities, sample): file_name
                for file_name, sample in todo
            }
            for future in as_completed(futures):
                file_name = futures[future]
                try:
                    entities, relations, meta = future.result()
                except Exception as exc:  # noqa: BLE001
                    entities, relations = [], []
                    meta = {
                        "status": "error",
                        "error": f"{type(exc).__name__}: {exc}",
                        "model": None,
                    }
                logger.info(
                    "event=ingest.extract.done file=%s status=%s entities=%d relations=%d",
                    file_name,
                    meta.get("status"),
                    len(entities),
                    len(relations),
                )
                self._append_extract_log(
                    source_dir,
                    {
                        "file": file_name,
                        "status": meta.get("status"),
                        "model": meta.get("model"),
                        "error": meta.get("error"),
                        "entities": entities,
                        "relations": relations,
                    },
                )
                # Làm sạch trước khi nhúng/ghi: bỏ ký tự Trung lẫn vào, bỏ tên
                # rỗng và quan hệ tự trỏ (dữ liệu rác từ LLM).
                for ent in entities:
                    ent["name"] = strip_cjk(str(ent.get("name", "")))
                    ent["description"] = strip_cjk(str(ent.get("description", "")))
                entities = [e for e in entities if e["name"]]
                for rel in relations:
                    rel["source"] = strip_cjk(str(rel.get("source", "")))
                    rel["target"] = strip_cjk(str(rel.get("target", "")))
                    rel["description"] = strip_cjk(str(rel.get("description", "")))
                relations = [
                    r
                    for r in relations
                    if r["source"] and r["target"] and r["source"] != r["target"]
                ]
                for ent in entities:
                    ent.setdefault("relations", [])
                for rel in relations:
                    src = rel.get("source", "")
                    for ent in entities:
                        if ent.get("name") == src:
                            ent["relations"].append(rel)

                embeddings = None
                if entities:
                    try:
                        embeddings = self._embedder.embed(
                            [
                                entity_embedding_text(
                                    e.get("name", ""), e.get("description", "")
                                )
                                for e in entities
                            ]
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "event=ingest.embed.error stage=dedup reason=%s",
                            type(exc).__name__,
                        )
                        embeddings = None
                merged, merge_count = merge_entities(
                    entities,
                    threshold=self._settings.dedup_threshold,
                    embeddings=embeddings,
                )
                report.merge_count += merge_count
                report.entity_count += len(merged)
                try:
                    merged_embeddings = self._embedder.embed(
                        [
                            entity_embedding_text(
                                e.get("name", ""), e.get("description", "")
                            )
                            for e in merged
                        ]
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "event=ingest.embed.error stage=upsert reason=%s",
                        type(exc).__name__,
                    )
                    merged_embeddings = [None] * len(merged)
                for ent, emb in zip(merged, merged_embeddings):
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
                        report.relation_count += 1

        logger.info("event=ingest.batch.done %s", json.dumps(report.to_dict(), ensure_ascii=False))
        self._event_bus.publish(
            KnowledgeIngested(
                chunks=report.chunk_count,
                entities=report.entity_count,
                relations=report.relation_count,
                duration_seconds=round(time.monotonic() - started, 3),
            )
        )
        return report

    def _append_extract_log(self, source_dir: Path, entry: dict) -> None:
        log_dir = source_dir / "processed"
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "extract_log.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _extract_entities(self, text: str) -> tuple[list[dict], list[dict], dict]:
        # Key là placeholder (chưa cấu hình) → bỏ qua ngay, đừng gọi API
        if not self._settings.qwen_api_key or self._settings.qwen_api_key.startswith(
            "your-"
        ):
            return [], [], {"status": "skipped", "model": None}
        prompt = EXTRACT_SYSTEM.format(types=", ".join(ENTITY_TYPES)) + f"\n\nĐoạn văn bản:\n{text[:4000]}"
        models = [
            m.strip()
            for m in self._settings.answer_model.split(",")
            if m.strip()
        ]
        last_error = "không có model"
        for model in models:
            for attempt in range(2):
                try:
                    response = requests.post(
                        f"{self._settings.qwen_base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self._settings.qwen_api_key}"},
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0,
                        },
                        timeout=90,
                    )
                    if response.status_code == 429 or response.status_code >= 500:
                        last_error = f"HTTP {response.status_code}"
                        time.sleep(2**attempt)
                        continue
                    if response.status_code >= 400:
                        last_error = f"HTTP {response.status_code}: {response.text[:150]}"
                        break  # chuyển model tiếp
                    content = response.json()["choices"][0]["message"]["content"]
                    # một số model bọc JSON trong ```json ... ```
                    if content.strip().startswith("```"):
                        content = (
                            content.strip()
                            .removeprefix("```json")
                            .removeprefix("```")
                            .removesuffix("```")
                        )
                    data = json.loads(content)
                    entities = data.get("entities", []) or []
                    relations = data.get("relations", []) or []
                    valid_entities = [
                        e
                        for e in entities
                        if e.get("entity_type") in ENTITY_TYPES and e.get("name")
                    ]
                    return valid_entities, relations, {"status": "ok", "model": model}
                except Exception as exc:  # noqa: BLE001
                    last_error = f"{type(exc).__name__}: {exc}"
                    logger.warning(
                        "event=ingest.extract.exception model=%s error=%s",
                        model,
                        last_error,
                    )
                    break  # timeout/mạng → sang model tiếp
        return [], [], {"status": "error", "error": last_error, "model": None}
