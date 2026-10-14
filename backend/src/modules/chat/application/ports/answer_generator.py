from __future__ import annotations

from typing import Protocol


class AnswerGeneratorPort(Protocol):
    def generate(self, prompt: str) -> str: ...


class EmbedderPort(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
