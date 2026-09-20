"""A privacy-first SQLite memory foundation.

The store deliberately starts with explainable lexical retrieval. Its stable
interface lets a later Qwen embedding + LanceDB adapter replace the ranking
layer without exposing memories to a cloud service.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3
from typing import Iterable


@dataclass(frozen=True)
class MemoryRecord:
    id: int
    content: str
    category: str
    importance: float
    confidence: float
    created_at: datetime


class MemoryManager:
    """Store and retrieve explicit local memories with transparent scoring."""

    def __init__(self, path: str | Path = "data/calvin.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_store()

    def remember(self, content: str, *, category: str = "personal", importance: float = 0.5,
                 confidence: float = 1.0) -> MemoryRecord:
        content = content.strip()
        if not content:
            raise ValueError("Memory content cannot be empty.")
        importance = max(0.0, min(1.0, importance))
        confidence = max(0.0, min(1.0, confidence))
        now = datetime.now(timezone.utc)
        with sqlite3.connect(self.path) as connection:
            existing = connection.execute(
                "SELECT id FROM memories WHERE content = ? AND category = ?", (content, category)
            ).fetchone()
            if existing:
                connection.execute(
                    "UPDATE memories SET importance = ?, confidence = ?, updated_at = ? WHERE id = ?",
                    (importance, confidence, now.isoformat(), existing[0]),
                )
                record_id = existing[0]
            else:
                cursor = connection.execute(
                    """INSERT INTO memories (content, category, importance, confidence, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (content, category, importance, confidence, now.isoformat(), now.isoformat()),
                )
                record_id = cursor.lastrowid
        return MemoryRecord(record_id, content, category, importance, confidence, now)

    def retrieve(self, query: str, *, limit: int = 5) -> list[MemoryRecord]:
        """Return records using similarity + importance + recency + confidence."""
        query_words = set(_words(query))
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                "SELECT id, content, category, importance, confidence, created_at FROM memories"
            ).fetchall()
        scored: list[tuple[float, MemoryRecord]] = []
        now = datetime.now(timezone.utc)
        for row in rows:
            created_at = datetime.fromisoformat(row[5])
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            terms = set(_words(row[1]))
            similarity = len(query_words & terms) / max(1, len(query_words | terms))
            age_days = max(0.0, (now - created_at).total_seconds() / 86400)
            recency = 1 / (1 + age_days / 30)
            score = (0.55 * similarity) + (0.25 * row[3]) + (0.10 * recency) + (0.10 * row[4])
            scored.append((score, MemoryRecord(row[0], row[1], row[2], row[3], row[4], created_at)))
        return [record for _, record in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]

    def forget(self, memory_id: int) -> bool:
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        return cursor.rowcount > 0

    def _init_store(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    importance REAL NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )


def _words(value: str) -> Iterable[str]:
    return re.findall(r"[a-z0-9']+", value.lower())
