from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    """Cơ sở cho mọi sự kiện dùng chung — bất biến (frozen)."""


@dataclass(frozen=True)
class UserLoggedIn(Event):
    """Có người đăng nhập thành công."""

    user_id: str
    role: str


@dataclass(frozen=True)
class UserPasswordChanged(Event):
    """Người dùng đã đổi mật khẩu."""

    user_id: str


@dataclass(frozen=True)
class KnowledgeIngested(Event):
    """Nạp tri thức xong — chỉ kèm số liệu, không kèm nội dung tài liệu."""

    chunks: int
    entities: int
    relations: int
    duration_seconds: float
