from __future__ import annotations

import re


def chunk_text(
    text: str,
    *,
    chunk_size: int = 800,
    overlap: int = 120,
    metadata: dict | None = None,
) -> list[dict]:
    """Recursive-ish character chunking, ưu tiên cắt theo điều khoản."""
    base_meta = metadata or {}
    if not text.strip():
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size phải lớn hơn 0")
    if overlap >= chunk_size:
        raise ValueError("overlap phải nhỏ hơn chunk_size")

    # Ưu tiên cắt theo điều khoản (Điều x, Mục x, ...)
    sections = re.split(r"(?=\n(?:Điều|Mục|Chương)\s+\d+)", text)
    sections = [s.strip() for s in sections if s.strip()]

    chunks: list[dict] = []
    for section in sections:
        if len(section) <= chunk_size:
            if section:
                chunks.append(
                    {"text": section, "metadata": {**base_meta, "section": _title_of(section)}}
                )
            continue
        start = 0
        while start < len(section):
            end = min(start + chunk_size, len(section))
            piece = section[start:end].strip()
            if piece:
                chunks.append(
                    {"text": piece, "metadata": {**base_meta, "section": _title_of(section)}}
                )
            if end >= len(section):
                break
            start = end - overlap
    return chunks


def _title_of(section: str) -> str:
    first_line = section.split("\n", 1)[0].strip()
    return first_line[:120]
