from __future__ import annotations


def entity_embedding_text(name: str, description: str) -> str:
    """Chuỗi nhúng của thực thể — dùng thống nhất khi nạp và khi backfill (ADR-06)."""
    return f"{name} {description}"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine hai vector. Vector rỗng hoặc lệch chiều → 0."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def keyword_ratio(name: str, description: str, keywords: list[str]) -> float:
    """Tỷ lệ từ khóa xuất hiện trong tên + mô tả, về [0, 1]."""
    if not keywords:
        return 0.0
    hay = f"{name} {description}".lower()
    hit = sum(1 for kw in keywords if kw and kw.lower() in hay)
    return hit / len(keywords)


def score_entity(
    node: dict,
    query_vector: list[float],
    keywords: list[str],
    *,
    alpha: float,
) -> float:
    """ADR-06: score = α·semantic + (1−α)·keyword."""
    semantic = max(0.0, cosine_similarity(query_vector, node.get("embedding") or []))
    keyword = keyword_ratio(
        str(node.get("name") or ""), str(node.get("description") or ""), keywords
    )
    return alpha * semantic + (1.0 - alpha) * keyword


def rank_entities(
    nodes: list[dict],
    query_vector: list[float],
    keywords: list[str],
    *,
    alpha: float,
    limit: int,
) -> list[dict]:
    """Chấm điểm ADR-06 và lấy `limit` node cao nhất, xếp theo score giảm dần."""
    if limit <= 0:
        return []
    scored: list[dict] = []
    for node in nodes:
        name = str(node.get("name") or "")
        if not name:
            continue
        scored.append(
            {
                "name": name,
                "description": str(node.get("description") or ""),
                "entity_type": str(node.get("entity_type") or ""),
                "score": score_entity(node, query_vector, keywords, alpha=alpha),
            }
        )
    scored.sort(key=lambda n: n["score"], reverse=True)
    return scored[:limit]
