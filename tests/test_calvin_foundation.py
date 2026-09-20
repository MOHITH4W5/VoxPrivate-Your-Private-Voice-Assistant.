"""Tests for CALVIN's local-first foundation."""

from src.commands.executor import CommandExecutor
from src.conversation import ConversationEngine
from src.memory import MemoryManager
from src.security import PermissionManager
from src.utils.config import Config


def _config(tmp_path):
    return Config(
        {
            "privacy": {"memory_path": str(tmp_path / "calvin.db")},
            "permissions": {"default": "ask", "allow": ["time", "date", "help", "stop"], "deny": []},
        }
    )


def test_sensitive_device_action_requires_confirmation(tmp_path):
    decision = PermissionManager(_config(tmp_path)).decide("shutdown")
    assert not decision.allowed
    assert decision.needs_confirmation


def test_safe_action_is_allowed_by_policy(tmp_path):
    decision = PermissionManager(_config(tmp_path)).decide("time")
    assert decision.allowed
    assert not decision.needs_confirmation


def test_executor_does_not_run_unconfirmed_device_action(tmp_path):
    response = CommandExecutor(_config(tmp_path)).execute("shutdown", {})
    assert "confirmation" in response.lower()


def test_local_memory_retrieves_relevant_fact(tmp_path):
    memory = MemoryManager(tmp_path / "memory.db")
    memory.remember("Mohith is building a private voice assistant.", importance=0.9)
    memory.remember("The weather is pleasant.")
    results = memory.retrieve("voice assistant project")
    assert results[0].content == "Mohith is building a private voice assistant."


def test_conversation_engine_uses_local_memory(tmp_path):
    memory = MemoryManager(tmp_path / "memory.db")
    memory.remember("Your preferred assistant name is Calvin.")
    response = ConversationEngine(memory).respond("What is my preferred assistant name?")
    assert "Calvin" in response.text
