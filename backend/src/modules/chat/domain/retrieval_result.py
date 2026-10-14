from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetrievedChunk:
    """Một đoạn tri thức truy xuất được."""

    text: str
    score: float
    source: str = ""
    metadata: dict = field(default_factory=dict)

    def citation(self) -> str:
        if self.source:
            return self.source
        return self.metadata.get("document", "") or self.metadata.get("sheet", "")


@dataclass(frozen=True)
class GraphContext:
    nodes: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.nodes and not self.edges

    def best_score(self) -> float:
        if not self.nodes:
            return 0.0
        return max(float(n.get("score", 0.0)) for n in self.nodes)


@dataclass(frozen=True)
class RetrievedContext:
    mode: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    graph: GraphContext = field(default_factory=GraphContext)

    def is_empty(self) -> bool:
        return not self.chunks and self.graph.is_empty()

    def best_score(self) -> float:
        scores = [c.score for c in self.chunks]
        if not self.graph.is_empty():
            scores.append(self.graph.best_score())
        return max(scores) if scores else 0.0
