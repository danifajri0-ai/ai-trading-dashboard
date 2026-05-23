from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any


class SQLiteStore:
    def __init__(self, db_path: str | Path = "data/cockpit/cockpit.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def save_signal_history(self, payload: dict[str, Any]) -> int:
        return self._insert("signal_history", payload)

    def save_snapshot(self, payload: dict[str, Any]) -> int:
        return self._insert("snapshot", payload)

    def read_records(self, record_type: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        query = "SELECT id, record_type, recorded_at, payload FROM cockpit_records"
        params: list[Any] = []
        if record_type is not None:
            query += " WHERE record_type = ?"
            params.append(record_type)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(query, params).fetchall()

        records: list[dict[str, Any]] = []
        for row in rows:
            payload = _safe_json_loads(row[3])
            records.append(
                {
                    "id": row[0],
                    "record_type": row[1],
                    "recorded_at": row[2],
                    "payload": payload,
                }
            )
        return records

    def _insert(self, record_type: str, payload: dict[str, Any]) -> int:
        recorded_at = datetime.now(timezone.utc).isoformat()
        serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                "INSERT INTO cockpit_records (record_type, recorded_at, payload) VALUES (?, ?, ?)",
                (record_type, recorded_at, serialized),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cockpit_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_type TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_cockpit_records_type ON cockpit_records(record_type)"
            )
            connection.commit()


def _safe_json_loads(value: object) -> dict[str, Any]:
    if not isinstance(value, str):
        return {}
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}
