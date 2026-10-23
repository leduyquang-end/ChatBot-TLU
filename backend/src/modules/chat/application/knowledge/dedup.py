from __future__ import annotations

from src.modules.chat.domain.graph_scoring import cosine_similarity


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
    # Giai đoạn 1: theo tên (không phân biệt hoa/thường — "Học kỳ" = "học kỳ")
    by_name: dict[str, dict] = {}
    order: list[str] = []
    for ent in entities:
        name = ent.get("name", "").strip()
        if not name:
            continue
        key = name.casefold()
        if key in by_name:
            by_name[key] = _merge_pair(by_name[key], ent)
            merges += 1
        else:
            by_name[key] = dict(ent)
            order.append(key)

    stage1 = [by_name[n] for n in order]

    # Giai đoạn 2: theo cosine của embeddings (nếu có)
    if embeddings and len(embeddings) == len(entities):
        # map tên → vector đầu tiên gặp được
        name_vec: dict[str, list[float]] = {}
        for ent, vec in zip(entities, embeddings):
            name = ent.get("name", "").strip()
            if name and name.casefold() not in name_vec:
                name_vec[name.casefold()] = vec

        merged_flags = [False] * len(stage1)
        result: list[dict] = []
        for i, ent in enumerate(stage1):
            if merged_flags[i]:
                continue
            for j in range(i + 1, len(stage1)):
                if merged_flags[j]:
                    continue
                va = name_vec.get(ent.get("name", "").strip().casefold())
                vb = name_vec.get(stage1[j].get("name", "").strip().casefold())
                if va and vb and cosine_similarity(va, vb) >= threshold:
                    ent = _merge_pair(ent, stage1[j])
                    merged_flags[j] = True
                    merges += 1
            result.append(ent)
        return result, merges

    return stage1, merges


def _merge_pair(a: dict, b: dict) -> dict:
    """Giữ mô tả dài hơn, tên của bản gặp trước, gộp relations."""
    keep = a if len(a.get("description", "")) >= len(b.get("description", "")) else b
    merged = dict(keep)
    merged["name"] = a.get("name", merged.get("name", ""))
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
