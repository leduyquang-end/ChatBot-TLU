from __future__ import annotations

from src.modules.chat.domain.conversation import Conversation


class InMemoryConversationStore:
    """Lịch sử hội thoại tạm trong RAM (A-02 chưa chốt).

    An toàn hơn lưu bền khi chưa quyết định nơi lưu và thời hạn.
    """

    def __init__(self) -> None:
        self._store: dict[str, Conversation] = {}

    def get_or_create(self, conversation_id: str, user_id: str) -> Conversation:
        conv = self._store.get(conversation_id)
        if conv is None:
            conv = Conversation(conversation_id=conversation_id, user_id=user_id)
            self._store[conversation_id] = conv
        return conv

    def save(self, conversation: Conversation) -> None:
        self._store[conversation.conversation_id] = conversation

    def list_for_user(self, user_id: str) -> list[Conversation]:
        return [c for c in self._store.values() if c.user_id == user_id]
