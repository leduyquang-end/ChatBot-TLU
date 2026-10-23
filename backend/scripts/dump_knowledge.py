#!/usr/bin/env python3
"""Xuất toàn bộ dữ liệu thật trong ChromaDB + Neo4j ra file JSON.

Usage:
    python backend/scripts/dump_knowledge.py

Đầu ra (data/processed/):
    chroma_export.json   — mọi chunk: id, text, metadata
    neo4j_export.json    — mọi node + relationship kèm properties
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]  # backend/
REPO_ROOT = ROOT.parents[0]
sys.path.insert(0, str(ROOT))

OUT_DIR = REPO_ROOT / "data" / "processed"


def export_chroma(settings) -> dict:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    parsed = urlparse(settings.chroma_url)
    client = chromadb.HttpClient(
        host=parsed.hostname or "localhost",
        port=parsed.port or 8000,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(settings.chroma_collection)

    emb = collection.get(limit=1, include=["embeddings"]).get("embeddings")
    embedding_dim = len(emb[0]) if emb is not None and len(emb) else None

    got = collection.get(include=["documents", "metadatas"])
    chunks = [
        {
            "id": cid,
            "text": text,
            "metadata": meta or {},
        }
        for cid, text, meta in zip(
            got.get("ids") or [],
            got.get("documents") or [],
            got.get("metadatas") or [],
        )
    ]
    return {
        "exported_at": _now(),
        "database": "chroma",
        "url": settings.chroma_url,
        "collection": settings.chroma_collection,
        "chunk_count": len(chunks),
        "embedding_dim": embedding_dim,
        "note": "embedding không export (mỗi chunk là 768 số thực, vô nghĩa khi đọc tay)",
        "chunks": chunks,
    }


def export_neo4j(settings) -> dict:
    from neo4j import GraphDatabase

    result: dict = {
        "exported_at": _now(),
        "database": "neo4j",
        "uri": settings.neo4j_uri,
        "node_count": 0,
        "relationship_count": 0,
        "nodes": [],
        "relationships": [],
        "note": None,
        "error": None,
    }
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            result["nodes"] = [
                {"labels": record["labels"], "properties": record["properties"]}
                for record in session.run(
                    "MATCH (n) RETURN labels(n) AS labels, properties(n) AS properties"
                )
            ]
            if result["nodes"]:
                result["relationships"] = [
                    {
                        "type": record["type"],
                        "from": {
                            "element_id": record["from_id"],
                            "name": record["from_name"],
                        },
                        "to": {
                            "element_id": record["to_id"],
                            "name": record["to_name"],
                        },
                        "properties": record["properties"],
                    }
                    for record in session.run(
                        """
                        MATCH (a)-[r]->(b)
                        RETURN type(r) AS type, properties(r) AS properties,
                               elementId(a) AS from_id,
                               coalesce(a.name, elementId(a)) AS from_name,
                               elementId(b) AS to_id,
                               coalesce(b.name, elementId(b)) AS to_name
                        """
                    )
                ]
        result["node_count"] = len(result["nodes"])
        result["relationship_count"] = len(result["relationships"])
        if result["node_count"] == 0:
            result["note"] = (
                "Graph rỗng: QWEN_API_KEY trong .env vẫn là placeholder nên pipeline "
                "bỏ qua trích xuất thực thể khi ingest. Nhập key thật rồi chạy lại "
                "ingest để nạp Neo4j."
            )
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        driver.close()
    return result


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Da ghi: {path}")


def main() -> int:
    from dotenv import load_dotenv

    for candidate in (REPO_ROOT / ".env", ROOT / ".env"):
        if candidate.exists():
            load_dotenv(candidate)
            break

    from src.platform.logging.setup import setup_logging
    from src.shared.config.settings import get_settings

    settings = get_settings()
    setup_logging("WARNING")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chroma = export_chroma(settings)
    neo4j = export_neo4j(settings)
    _write(OUT_DIR / "chroma_export.json", chroma)
    _write(OUT_DIR / "neo4j_export.json", neo4j)
    print(
        f"Chroma: {chroma['chunk_count']} chunk | "
        f"Neo4j: {neo4j['node_count']} node, {neo4j['relationship_count']} cạnh"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
