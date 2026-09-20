"""Small, dependency-free data types shared between CALVIN modules."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AssistantState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    STOPPED = "stopped"


@dataclass(frozen=True)
class ConversationTurn:
    role: str
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AssistantResponse:
    text: str
    state: AssistantState = AssistantState.IDLE
    needs_confirmation: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
