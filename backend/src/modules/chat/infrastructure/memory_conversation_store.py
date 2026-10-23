from __future__ import annotations

import logging
import uuid

from src.modules.chat.domain.conversation import Conversation

logger = logging.getLogger(__name__)


class InMemoryConversationStore:
    """Lịch sử hội thoại tạm trong RAM (A-02 chưa chốt).

    An toàn hơn lưu bền khi chưa quyết định nơi lưu và thời hạn.
    Chỉ `save()` mới đưa conversation vào bộ nhớ — `get_or_create()` không ghi
    (hỏi với id lạ không phình bộ nhớ); id đã thuộc user khác không được gộp.
    """

    def __init__(self) -> None:
        self._store: dict[str, Conversation] = {}

    def get_or_create(self, conversation_id: str, user_id: str) -> Conversation:
        conv = self._store.get(conversation_id)
        if conv is None:
            return Conversation(conversation_id=conversation_id, user_id=user_id)
        if conv.user_id == user_id:
            return conv
        # id đang sở hữu bởi user khác: không đọc, không ghi vào cuộc hội thoại đó,
        # trả về cuộc hội thoại MỚI (chưa lưu) — pipeline trả id mới trong response.
        logger.warning(
            "event=chat.conversation.foreign_id requested=%s user=%s", conversation_id, user_id
        )
        return Conversation(conversation_id=str(uuid.uuid4()), user_id=user_id)

    def save(self, conversation: Conversation) -> None:
        self._store[conversation.conversation_id] = conversation

    def list_for_user(self, user_id: str) -> list[Conversation]:
        return [c for c in self._store.values() if c.user_id == user_id]
