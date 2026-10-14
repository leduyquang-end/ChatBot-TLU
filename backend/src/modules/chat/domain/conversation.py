from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Conversation:
    conversation_id: str
    user_id: str
    turns: list[dict] = field(default_factory=list)

    def add_turn(self, question: str, answer: str) -> None:
        self.turns.append({"role": "user", "content": question})
        self.turns.append({"role": "assistant", "content": answer})

    def history(self, max_turns: int) -> list[dict]:
        """Trả về tối đa max_turns lượt (mỗi lượt = user + assistant)."""
        max_messages = max_turns * 2
        if max_turns <= 0:
            return []
        return self.turns[-max_messages:]
