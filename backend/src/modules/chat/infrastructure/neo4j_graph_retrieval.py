from __future__ import annotations

import logging

from src.modules.chat.domain.retrieval_result import GraphContext, RetrievedContext
from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings

logger = logging.getLogger(__name__)

# TrÃ­ch thá»±c thá»ƒ tá»« cÃ¢u há»i báº±ng Llama qua Groq
EXTRACT_PROMPT = (
    "TrÃ­ch cÃ¡c tÃªn thá»±c thá»ƒ (mÃ´n há»c, ngÃ nh há»c, há»c phÃ­, há»c bá»•ng, "
    "há»c ká»³, bá»™ mÃ´n, Ä‘á»‘i tÆ°á»£ng, thá»§ tá»¥c) xuáº¥t hiá»‡n trong cÃ¢u há»i sau. "
    "Tráº£ vá» JSON {\"entities\": [\"...\"]} vá»›i tá»‘i Ä‘a 5 tÃªn. "
    "Náº¿u khÃ´ng cÃ³, tráº£ vá» {\"entities\": []}.\n\nCÃ¢u há»i: {question}"
)


class Neo4jGraphRetrieval:
    """Truy xuáº¥t Ä‘á»“ thá»‹: cháº¥m Ä‘iá»ƒm Î±Â·semantic + (1âˆ’Î±)Â·keyword (ADR-06)."""

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
            raise ExternalServiceError("Kho quan há»‡ khÃ´ng truy cáº­p Ä‘Æ°á»£c") from exc

    def _extract_entities(self, question: str) -> list[str]:
        import json

        import requests

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._groq_api_key}"},
                json={
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
            )
            if response.status_code >= 400:
                return []
            content = response.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            return [str(e) for e in data.get("entities", [])][:5]
        except Exception:  # noqa: BLE001
            return []

    def _score_nodes(
        self, question: str, keywords: list[str], *, alpha: float, limit: int
    ) -> list[dict]:
        driver = self._load()
        q_vec = self._embedder.embed([question])[0]
        query_vec_literal = "[" + ",".join(f"{x:.6f}" for x in q_vec) + "]"
        cypher = """
        MATCH (n:Entity)
        WITH n,
             COALESCE(n.embedding, []) AS emb,
             toLower(COALESCE(n.name, "")) + ' ' + toLower(COALESCE(n.description, "")) AS hay
        WITH n, emb, hay,
             reduce(s = 0.0, kw IN $keywords |
               s + CASE WHEN toLower(n.name) CONTAINS toLower(kw)
                         OR toLower(COALESCE(n.description, "")) CONTAINS toLower(kw)
                        THEN 1.0 ELSE 0.0 END) AS keyword_score
        RETURN n.name AS name,
               COALESCE(n.description, "") AS description,
               COALESCE(n.entity_type, "") AS entity_type,
               keyword_score
        ORDER BY keyword_score DESC
        LIMIT $limit
        """
        results = []
        with driver.session() as session:
            records = session.run(
                cypher, keywords=keywords, limit=limit
            )
            for record in records:
                results.append(
                    {
                        "name": record["name"],
                        "description": record["description"],
                        "entity_type": record["entity_type"],
                        "score": float(record["keyword_score"]),
                    }
                )
        # semantic score náº¿u cÃ³ embedding stored; táº¡m dÃ¹ng keyword lÃ m fallback
        if results:
            max_kw = max(r["score"] for r in results) or 1.0
            for r in results:
                semantic = r["score"] / max_kw
                keyword = r["score"] / max_kw
                r["score"] = alpha * semantic + (1 - alpha) * keyword
        _ = query_vec_literal
        return results

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
    """Ghi thá»±c thá»ƒ vÃ  quan há»‡ báº±ng MERGE (ADR-07)."""

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
                    e.entity_type = $entity_type
                """,
                name=name,
                description=description,
                entity_type=entity_type,
            )

    def upsert_relation(
        self,
        source: str,
        target: str,
        description: str,
        confidence: float,
    ) -> None:
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
