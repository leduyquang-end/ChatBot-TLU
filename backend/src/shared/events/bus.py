from __future__ import annotations

import logging
import threading
from collections import defaultdict
from collections.abc import Callable
from typing import TypeVar

from src.shared.events.types import Event

logger = logging.getLogger(__name__)

E = TypeVar("E", bound=Event)


class EventBus:
    """Bus sự kiện trong tiến trình — pub/sub, thread-safe.

    Module không gọi chéo trực tiếp; module bắn sự kiện qua đây, module khác
    "nghe" sự kiện mình cần (AGENT.md mục: shared/events).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._handlers: dict[type[Event], list[Callable[[Event], None]]] = (
            defaultdict(list)
        )

    def subscribe(self, event_type: type[E], handler: Callable[[E], None]) -> None:
        """Đăng ký nghe sự kiện theo đúng loại. Đăng ký lặp lại bị bỏ qua."""
        with self._lock:
            handlers = self._handlers[event_type]
            if handler not in handlers:
                handlers.append(handler)

    def unsubscribe(self, event_type: type[E], handler: Callable[[E], None]) -> None:
        """Bỏ đăng ký — gọi lần thứ hai cũng an toàn (không lỗi)."""
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)

    def publish(self, event: E) -> int:
        """Gửi sự kiện đến mọi handler của đúng loại (theo `type(event)`).

        Handler lỗi không được làm hỏng handler khác hay người bắn.
        Trả về số handler đã gọi.
        """
        with self._lock:
            handlers = list(self._handlers.get(type(event), ()))
        for handler in handlers:
            try:
                handler(event)
            except Exception:  # noqa: BLE001 - cách ly lỗi handler là chủ đích
                logger.warning(
                    "event=events.handler_failed type=%s handler=%s",
                    type(event).__name__,
                    getattr(handler, "__name__", repr(handler)),
                )
        return len(handlers)

    def clear(self) -> None:
        """Gỡ hết đăng ký — dùng cho test."""
        with self._lock:
            self._handlers.clear()


_BUS: EventBus | None = None
_BUS_LOCK = threading.Lock()


def get_event_bus() -> EventBus:
    """Bus dùng chung toàn ứng dụng (an toàn luồng — 2 request cold start không tạo đôi)."""
    global _BUS
    if _BUS is None:
        with _BUS_LOCK:
            if _BUS is None:
                _BUS = EventBus()
    return _BUS


def reset_event_bus() -> None:
    """Thay bus mới — dùng cho test."""
    global _BUS
    with _BUS_LOCK:
        _BUS = None
