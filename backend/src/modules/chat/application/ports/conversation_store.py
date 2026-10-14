from __future__ import annotations

from typing import Protocol

from src.modules.chat.domain.conversation import Conversation


class ConversationStorePort(Protocol):
    def get_or_create(self, conversation_id: str, user_id: str) -> Conversation: ...

    def save(self, conversation: Conversation) -> None: ...

    def list_for_user(self, user_id: str) -> list[Conversation]: ...
