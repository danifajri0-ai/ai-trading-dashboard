from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


DEFAULT_HISTORY_PATH = Path("data/cockpit/signal_history.jsonl")


def append_signal_snapshot(
    snapshot: dict[str, Any],
    history_path: str | Path = DEFAULT_HISTORY_PATH,
) -> dict[str, Any]:
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **snapshot,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return {"status": "available", "path": str(path), "recorded": True}


def read_performance_summary(
    history_path: str | Path = DEFAULT_HISTORY_PATH,
    symbol: str | None = None,
    timeframe: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    path = Path(history_path)
    if not path.exists():
        return _not_available("Signal history file does not exist yet.")

    records = _read_records(path, limit=limit)
    if symbol is not None:
        records = [record for record in records if str(record.get("symbol")) == symbol]
    if timeframe is not None:
        records = [record for record in records if str(record.get("timeframe")) == timeframe]

    if not records:
        return _not_available("No matching signal history records are available.")

    actionable = [record for record in records if str(record.get("signal", "")).upper() not in {"", "WAIT"}]
    blocked = [record for record in records if record.get("valid_signal") is False]
    confidence_values = [
        float(record["confidence"])
        for record in records
        if _is_number(record.get("confidence"))
    ]
    avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else None

    return {
        "status": "available",
        "sample_size": len(records),
        "actionable_signals": len(actionable),
        "blocked_or_invalid_signals": len(blocked),
        "average_confidence": round(avg_confidence, 2) if avg_confidence is not None else None,
        "caveat": (
            "Performance memory is an operational signal log, not a realized PnL ledger. "
            "It should not be interpreted as proof of profitability."
        ),
    }


def _not_available(reason: str) -> dict[str, Any]:
    return {
        "status": "not_available",
        "sample_size": 0,
        "actionable_signals": 0,
        "blocked_or_invalid_signals": 0,
        "average_confidence": None,
        "caveat": (
            "Performance memory is unavailable or too small. "
            "Do not infer historical profitability from missing records."
        ),
        "notes": [reason],
    }


def _read_records(path: Path, limit: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()[-limit:]
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def _is_number(value: object) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True
