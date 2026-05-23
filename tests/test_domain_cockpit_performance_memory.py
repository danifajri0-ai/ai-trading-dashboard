from __future__ import annotations

from domain.cockpit.performance_memory import append_signal_snapshot, read_performance_summary


def test_performance_memory_is_safe_when_file_missing(tmp_path) -> None:
    history_path = tmp_path / "signal_history.jsonl"

    result = read_performance_summary(history_path, symbol="BTCUSD", timeframe="H1")

    assert result["status"] == "not_available"
    assert result["sample_size"] == 0
    assert result["caveat"]


def test_performance_memory_appends_and_summarizes_records(tmp_path) -> None:
    history_path = tmp_path / "signal_history.jsonl"
    append_signal_snapshot(
        {
            "symbol": "BTCUSD",
            "timeframe": "H1",
            "signal": "BUY",
            "confidence": 72.0,
            "valid_signal": True,
        },
        history_path=history_path,
    )
    append_signal_snapshot(
        {
            "symbol": "BTCUSD",
            "timeframe": "H1",
            "signal": "WAIT",
            "confidence": 45.0,
            "valid_signal": False,
        },
        history_path=history_path,
    )

    result = read_performance_summary(history_path, symbol="BTCUSD", timeframe="H1")

    assert result["status"] == "available"
    assert result["sample_size"] == 2
    assert result["actionable_signals"] == 1
    assert result["blocked_or_invalid_signals"] == 1
    assert result["average_confidence"] == 58.5
    assert "not a realized pnl ledger" in result["caveat"].lower()
