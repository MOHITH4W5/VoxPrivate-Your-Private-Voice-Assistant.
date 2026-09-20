"""Local conversation context with an optional local-LLM handoff point."""

from __future__ import annotations

from collections import deque
from typing import Callable

from src.core.types import AssistantResponse, ConversationTurn
from src.memory import MemoryManager


class ConversationEngine:
    """Maintains short-term context and prepares grounded local responses."""

    def __init__(self, memory: MemoryManager, responder: Callable[[str], str] | None = None,
                 max_turns: int = 12):
        self.memory = memory
        self.responder = responder
        self.turns: deque[ConversationTurn] = deque(maxlen=max_turns)

    def respond(self, user_text: str) -> AssistantResponse:
        self.turns.append(ConversationTurn(role="user", content=user_text))
        memories = self.memory.retrieve(user_text, limit=3)
        context = self._build_context(user_text, memories)
        text = self.responder(context) if self.responder else self._offline_fallback(user_text, memories)
        self.turns.append(ConversationTurn(role="assistant", content=text))
        return AssistantResponse(text=text, metadata={"memory_count": len(memories)})

    def _build_context(self, user_text: str, memories) -> str:
        history = "\n".join(f"{turn.role}: {turn.content}" for turn in self.turns)
        remembered = "\n".join(f"- {memory.content}" for memory in memories)
        return (
            "You are C.A.L.V.I.N, a private local assistant. Be warm, concise, and truthful. "
            "Do not claim to have used online services.\n"
            f"Relevant memory:\n{remembered or '- None'}\nConversation:\n{history}\nuser: {user_text}"
        )

    @staticmethod
    def _offline_fallback(user_text: str, memories) -> str:
        if memories:
            return f"I remember {memories[0].content}. What would you like to do next?"
        return f"I heard: {user_text}. My local language model is not configured yet, but I am ready to help with device-safe requests."
