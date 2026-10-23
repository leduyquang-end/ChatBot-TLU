from __future__ import annotations

import logging

from src.modules.chat.domain.graph_scoring import rank_entities
from src.modules.chat.domain.retrieval_result import GraphContext, RetrievedContext
from src.modules.chat.infrastructure.retry import post_json_with_retry
from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings

logger = logging.getLogger(__name__)

# Trích thực thể từ câu hỏi bằng Qwen qua Groq (dấu {} phải escape khi dùng format)
EXTRACT_PROMPT = (
    "Trích các tên thực thể (môn học, ngành học, học phí, học bổng, "
    "học kỳ, bộ môn, đối tượng, thủ tục) xuất hiện trong câu hỏi sau. "
    "Trả về JSON {{\"entities\": [\"...\"]}} với tối đa 5 tên. "
    "Nếu không có, trả về {{\"entities\": []}}.\n\nCâu hỏi: {question}"
)


class Neo4jGraphRetrieval:
    """Truy xuất đồ thị: chấm điểm α·semantic + (1−α)·keyword (ADR-06)."""

    def __init__(self, settings: Settings, embedder, groq_api_key: str) -> None:
        self._settings = settings
        self._embedder = embedder
        self._groq_api_key = groq_api_key
        self._driver = None

    def _load(self):
        if self._driver is None:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(
                self._settings.neo4j_uri,
                auth=(self._settings.neo4j_user, self._settings.neo4j_password),
            )
        return self._driver

    def retrieve(self, question: str, *, alpha: float, fetch_k: int) -> RetrievedContext:
        try:
            entities = self._extract_entities(question)
            if not entities:
                entities = [w for w in question.split() if len(w) > 3][:3]
            nodes = self._score_nodes(question, entities, alpha=alpha, limit=fetch_k)
            edges = []
            if nodes:
                edges = self._fetch_edges([n["name"] for n in nodes])
            return RetrievedContext(
                mode="Graph",
                graph=GraphContext(nodes=nodes, edges=edges),
            )
        except ExternalServiceError:
            raise
        except Exception as exc:
            logger.error("event=chat.retrieval.graph.error reason=%s", type(exc).__name__)
            raise ExternalServiceError("Kho quan hệ không truy cập được") from exc

    def _extract_entities(self, question: str) -> list[str]:
        import json

        try:
            response = post_json_with_retry(
                "https://api.groq.com/openai/v1/chat/completions",
                service="groq_entity_extract",
                headers={"Authorization": f"Bearer {self._groq_api_key}"},
                payload={
                    "model": self._settings.router_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": EXTRACT_PROMPT.format(question=question),
                        }
                    ],
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                },
                timeout=self._settings.request_timeout_seconds,
                max_retries=self._settings.max_retries,
                backoff_seconds=self._settings.retry_backoff_seconds,
            )
            content = response.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            entities = data.get("entities", [])
            if not isinstance(entities, list):
                return []
            return [str(e) for e in entities][:5]
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "event=chat.entities.fallback reason=%s", type(exc).__name__
            )
            return []

    def _score_nodes(
        self, question: str, keywords: list[str], *, alpha: float, limit: int
    ) -> list[dict]:
        """ADR-06: score = α·semantic + (1−α)·keyword, semantic = cosine với embedding node."""
        driver = self._load()
        query_vec = self._embedder.embed([question])[0]
        cypher = """
        MATCH (n:Entity)
        RETURN n.name AS name,
               COALESCE(n.description, "") AS description,
               COALESCE(n.entity_type, "") AS entity_type,
               n.embedding AS embedding
        """
        nodes: list[dict] = []
        with driver.session() as session:
            for record in session.run(cypher):
                nodes.append(
                    {
                        "name": record["name"],
                        "description": record["description"],
                        "entity_type": record["entity_type"],
                        "embedding": record["embedding"],
                    }
                )
        return rank_entities(nodes, query_vec, keywords, alpha=alpha, limit=limit)

    def _fetch_edges(self, names: list[str]) -> list[dict]:
        driver = self._load()
        cypher = """
        MATCH (a:Entity)-[r]->(b:Entity)
        WHERE a.name IN $names OR b.name IN $names
        RETURN a.name AS source, b.name AS target,
               COALESCE(r.description, type(r)) AS description,
               COALESCE(r.confidence, 0.0) AS confidence
        LIMIT 50
        """
        edges = []
        with driver.session() as session:
            for record in session.run(cypher, names=names):
                edges.append(
                    {
                        "source": record["source"],
                        "target": record["target"],
                        "description": record["description"],
                        "confidence": float(record["confidence"]),
                    }
                )
        return edges


class Neo4jGraphWriter:
    """Ghi thực thể và quan hệ bằng MERGE (ADR-07)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._driver = None

    def _load(self):
        if self._driver is None:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(
                self._settings.neo4j_uri,
                auth=(self._settings.neo4j_user, self._settings.neo4j_password),
            )
        return self._driver

    def upsert_entity(
        self, name: str, description: str, entity_type: str, embedding: list[float] | None = None
    ) -> None:
        driver = self._load()
        with driver.session() as session:
            session.run(
                """
                MERGE (e:Entity {name: $name})
                SET e.description = CASE
                      WHEN size($description) > size(COALESCE(e.description, ''))
                      THEN $description ELSE COALESCE(e.description, $description) END,
                    e.entity_type = $entity_type,
                    e.embedding = COALESCE($embedding, e.embedding)
                """,
                name=name,
                description=description,
                entity_type=entity_type,
                embedding=embedding,
            )

    def upsert_relation(
        self,
        source: str,
        target: str,
        description: str,
        confidence: float,
    ) -> None:
        if not source or not target or source == target:
            # quan hệ tự trỏ/rỗng: rác trích xuất, không ghi
            return
        driver = self._load()
        with driver.session() as session:
            session.run(
                """
                MATCH (a:Entity {name: $source})
                MATCH (b:Entity {name: $target})
                MERGE (a)-[r:RELATES_TO]->(b)
                SET r.description = CASE
                      WHEN size($description) > size(COALESCE(r.description, ''))
                      THEN $description ELSE COALESCE(r.description, $description) END,
                    r.confidence = CASE
                      WHEN $confidence > COALESCE(r.confidence, 0.0)
                      THEN $confidence ELSE COALESCE(r.confidence, $confidence) END
                """,
                source=source,
                target=target,
                description=description,
                confidence=confidence,
            )
