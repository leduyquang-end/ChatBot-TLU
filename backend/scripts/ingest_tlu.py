#!/usr/bin/env python3
"""Nạp tri thức TLU (QT-02). Chạy thủ công theo đợt.

Usage:
    python scripts/ingest_tlu.py [thư mục tài liệu]
Mặc định: data/source
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # backend/
REPO_ROOT = ROOT.parents[0]  # repo root
sys.path.insert(0, str(ROOT))


def main() -> int:
    from dotenv import load_dotenv

    for candidate in (REPO_ROOT / ".env", ROOT / ".env"):
        if candidate.exists():
            load_dotenv(candidate)
            break

    from src.modules.chat.application.knowledge.pipeline import KnowledgeIngestPipeline
    from src.modules.chat.infrastructure.chroma_retrieval import ChromaVectorRetrieval
    from src.modules.chat.infrastructure.hf_embedder import SentenceTransformerEmbedder
    from src.modules.chat.infrastructure.neo4j_graph_retrieval import Neo4jGraphWriter
    from src.platform.logging.audit import register_audit_handlers
    from src.platform.logging.setup import setup_logging
    from src.shared.config.settings import get_settings
    from src.shared.events import get_event_bus

    # .resolve(): Word COM (file .doc) không tự nối được đường dẫn tương đối
    source = (Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "data" / "source").resolve()
    if not source.exists():
        print(f"Thư mục tài liệu không tồn tại: {source}")
        return 1

    settings = get_settings()
    setup_logging(settings.log_level)
    register_audit_handlers(get_event_bus())

    embedder = SentenceTransformerEmbedder(settings)
    vector_store = ChromaVectorRetrieval(settings, embedder)
    graph_writer = Neo4jGraphWriter(settings)

    pipeline = KnowledgeIngestPipeline(
        settings,
        vector_store=vector_store,
        graph_writer=graph_writer,
        embedder=embedder,
        event_bus=get_event_bus(),
    )
    report = pipeline.run(source)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
