from __future__ import annotations

from enum import Enum


class RetrievalMode(str, Enum):
    """Bốn cách tìm theo QT-01 / AGENTS mục 5.2."""

    VECTOR = "Vector"
    GRAPH = "Graph"
    HYBRID = "Hybrid"
    NONE = "None"

    @classmethod
    def from_label(cls, label: str) -> "RetrievalMode":
        """Parse nhãn từ router. Sai định dạng → Vector (ADR-08, BR-03)."""
        normalized = (label or "").strip()
        for mode in cls:
            if normalized.lower() == mode.value.lower():
                return mode
        return cls.VECTOR
