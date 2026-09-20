"""Permission and local audit primitives.

No command or online tool should bypass this module.  The implementation is
intentionally local-only; it writes no telemetry and uses SQLite for audit data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import sqlite3


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class PermissionDecision:
    action: str
    allowed: bool
    needs_confirmation: bool
    reason: str
    risk: RiskLevel


class PermissionManager:
    """Evaluate local action permissions using allow/deny/ask policy lists."""

    _RISK_BY_ACTION = {
        "time": RiskLevel.LOW,
        "date": RiskLevel.LOW,
        "help": RiskLevel.LOW,
        "stop": RiskLevel.LOW,
        "screenshot": RiskLevel.MEDIUM,
        "create_file": RiskLevel.MEDIUM,
        "open_terminal": RiskLevel.MEDIUM,
        "open_browser": RiskLevel.MEDIUM,
        "play_music": RiskLevel.MEDIUM,
        "volume_up": RiskLevel.MEDIUM,
        "volume_down": RiskLevel.MEDIUM,
        "mute": RiskLevel.MEDIUM,
        "shutdown": RiskLevel.CRITICAL,
        "restart": RiskLevel.CRITICAL,
        "sleep": RiskLevel.HIGH,
    }

    def __init__(self, config, audit_path: str | Path | None = None):
        self._default = config.get("permissions", "default", default="ask")
        self._allow = set(config.get("permissions", "allow", default=[]))
        self._deny = set(config.get("permissions", "deny", default=[]))
        self._audit_path = Path(audit_path or config.get("privacy", "memory_path", default="data/calvin.db"))
        self._audit_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_audit_store()

    def decide(self, action: str, *, confirmed: bool = False) -> PermissionDecision:
        risk = self._RISK_BY_ACTION.get(action, RiskLevel.HIGH)
        if action in self._deny:
            decision = PermissionDecision(action, False, False, "This action is blocked by your policy.", risk)
        elif action in self._allow:
            decision = PermissionDecision(action, True, False, "Allowed by your policy.", risk)
        elif confirmed:
            decision = PermissionDecision(action, True, False, "Allowed for this confirmed request.", risk)
        elif self._default == "allow" and risk in {RiskLevel.LOW, RiskLevel.MEDIUM}:
            decision = PermissionDecision(action, True, False, "Allowed by your policy.", risk)
        else:
            decision = PermissionDecision(action, False, True, "Confirmation is required before this action.", risk)
        self._record(decision)
        return decision

    def _init_audit_store(self) -> None:
        with sqlite3.connect(self._audit_path) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS permission_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    action TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    allowed INTEGER NOT NULL,
                    needs_confirmation INTEGER NOT NULL,
                    reason TEXT NOT NULL
                )"""
            )

    def _record(self, decision: PermissionDecision) -> None:
        with sqlite3.connect(self._audit_path) as connection:
            connection.execute(
                "INSERT INTO permission_audit (created_at, action, risk, allowed, needs_confirmation, reason) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    decision.action,
                    decision.risk.value,
                    int(decision.allowed),
                    int(decision.needs_confirmation),
                    decision.reason,
                ),
            )
