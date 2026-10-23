from __future__ import annotations

import logging

from src.platform.logging.setup import get_logger, log_event
from src.shared.events import (
    EventBus,
    KnowledgeIngested,
    UserLoggedIn,
    UserPasswordChanged,
)

logger = get_logger(__name__)


def _log_user_logged_in(event: UserLoggedIn) -> None:
    log_event(
        logger,
        logging.INFO,
        "audit.user.logged_in",
        user_id=event.user_id,
        role=event.role,
    )


def _log_user_password_changed(event: UserPasswordChanged) -> None:
    log_event(
        logger,
        logging.INFO,
        "audit.user.password_changed",
        user_id=event.user_id,
    )


def _log_knowledge_ingested(event: KnowledgeIngested) -> None:
    log_event(
        logger,
        logging.INFO,
        "audit.knowledge.ingested",
        chunks=event.chunks,
        entities=event.entities,
        relations=event.relations,
        duration_s=event.duration_seconds,
    )


def register_audit_handlers(bus: EventBus) -> None:
    """Gắn handler audit vào bus — gọi ở composition root (app và script nạp tri thức).

    Đăng ký lặp lại an toàn: `EventBus.subscribe` bỏ qua handler đã có.
    """
    bus.subscribe(UserLoggedIn, _log_user_logged_in)
    bus.subscribe(UserPasswordChanged, _log_user_password_changed)
    bus.subscribe(KnowledgeIngested, _log_knowledge_ingested)
