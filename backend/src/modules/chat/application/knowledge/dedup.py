from __future__ import annotations

import math


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def merge_entities(
    entities: list[dict],
    *,
    threshold: float = 0.92,
    embeddings: list[list[float]] | None = None,
) -> tuple[list[dict], int]:
    """Khử trùng lặp hai giai đoạn (ADR-11).

    Giai đoạn 1: tên chính xác giống nhau.
    Giai đoạn 2: cosine >= threshold (nếu có embeddings).

    Trả về (danh sách đã gộp, số lần gộp).
    """
    merges = 0
    # Giai đoạn 1: theo tên chính xác
    by_name: dict[str, dict] = {}
    order: list[str] = []
    for ent in entities:
        name = ent.get("name", "").strip()
        if not name:
            continue
        if name in by_name:
            by_name[name] = _merge_pair(by_name[name], ent)
            merges += 1
        else:
            by_name[name] = dict(ent)
            order.append(name)

    stage1 = [by_name[n] for n in order]

    # Giai đoạn 2: theo cosine của embeddings (nếu có)
    if embeddings and len(embeddings) == len(entities):
        # map tên → vector đầu tiên见到
        name_vec: dict[str, list[float]] = {}
        for ent, vec in zip(entities, embeddings):
            name = ent.get("name", "").strip()
            if name and name not in name_vec:
                name_vec[name] = vec

        merged_flags = [False] * len(stage1)
        result: list[dict] = []
        for i, ent in enumerate(stage1):
            if merged_flags[i]:
                continue
            for j in range(i + 1, len(stage1)):
                if merged_flags[j]:
                    continue
                va = name_vec.get(ent.get("name", ""))
                vb = name_vec.get(stage1[j].get("name", ""))
                if va and vb and cosine(va, vb) >= threshold:
                    ent = _merge_pair(ent, stage1[j])
                    merged_flags[j] = True
                    merges += 1
            result.append(ent)
        return result, merges

    return stage1, merges


def _merge_pair(a: dict, b: dict) -> dict:
    """Giữ mô tả dài hơn, chuyển quan hệ, gộp relations."""
    keep = a if len(a.get("description", "")) >= len(b.get("description", "")) else b
    merged = dict(keep)
    relations = list(a.get("relations", [])) + list(b.get("relations", []))
    seen: set[tuple] = set()
    unique = []
    for rel in relations:
        key = (rel.get("source", ""), rel.get("target", ""))
        if key in seen:
            # giữ bản có confidence cao hơn
            for idx, existing in enumerate(unique):
                if (
                    (existing.get("source", ""), existing.get("target", "")) == key
                    and rel.get("confidence", 0) > existing.get("confidence", 0)
                ):
                    unique[idx] = rel
            continue
        seen.add(key)
        unique.append(rel)
    merged["relations"] = unique
    return merged
