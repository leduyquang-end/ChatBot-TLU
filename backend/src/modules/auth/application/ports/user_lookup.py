from __future__ import annotations

from typing import Protocol


class UserRecord(Protocol):
    """Phần auth cần biết về user — không import entity của module user."""

    id: str
    role: str


class UserLookup(Protocol):
    def find_by_id(self, user_id: str) -> UserRecord | None: ...
