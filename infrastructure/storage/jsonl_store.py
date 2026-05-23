from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


class JsonlStore:
    def __init__(self, path: str | Path = "data/cockpit/signal_history.jsonl") -> None:
        self.path = Path(path)

    def append_signal_history(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.append("signal_history", payload)

    def append_snapshot(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.append("snapshot", payload)

    def append(self, record_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "record_type": record_type,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        return {"status": "available", "path": str(self.path), "record_type": record_type}

    def read_records(self, record_type: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()[-limit:]
        for line in lines:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            if record_type is not None and record.get("record_type") != record_type:
                continue
            records.append(record)
        return records
