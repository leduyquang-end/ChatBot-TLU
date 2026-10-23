#!/usr/bin/env python3
"""Bổ sung embedding cho node Entity còn thiếu trong Neo4j (ADR-06).

Dùng cho các node nạp trước khi writer ghi e.embedding. Idempotent:
chỉ đụng node có n.embedding IS NULL. Chạy lại an toàn.

Usage:
    python scripts/backfill_entity_embeddings.py
"""
from __future__ import annotations

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

    from src.modules.chat.domain.graph_scoring import entity_embedding_text
    from src.modules.chat.infrastructure.hf_embedder import SentenceTransformerEmbedder
    from src.platform.logging.setup import setup_logging
    from src.shared.config.settings import get_settings

    settings = get_settings()
    setup_logging(settings.log_level)

    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    embedder = SentenceTransformerEmbedder(settings)
    batch_size = 64
    total = 0

    with driver.session() as session:
        while True:
            records = session.run(
                """
                MATCH (n:Entity)
                WHERE n.embedding IS NULL
                RETURN n.name AS name, COALESCE(n.description, "") AS description
                LIMIT $batch
                """,
                batch=batch_size,
            ).data()
            if not records:
                break
            vectors = embedder.embed(
                [entity_embedding_text(r["name"], r["description"]) for r in records]
            )
            for rec, vec in zip(records, vectors):
                session.run(
                    "MATCH (n:Entity {name: $name}) SET n.embedding = $embedding",
                    name=rec["name"],
                    embedding=vec,
                )
                total += 1

    driver.close()
    print(f"Đã ghi embedding cho {total} node")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
