from __future__ import annotations

import pandas as pd

from domain.cockpit.backtest_engine import run_lightweight_backtest


def test_backtest_engine_returns_lightweight_snapshot_for_actionable_signal() -> None:
    result = run_lightweight_backtest(
        _trend_frame(direction="up"),
        signal_rules={"signal": "BUY"},
        timeframe="H1",
        symbol="BTCUSD",
    )

    assert result["status"] == "available"
    assert result["sample_size"] >= 8
    assert 0 <= result["estimated_win_rate"] <= 100
    assert result["avg_rr"] is None or result["avg_rr"] >= 0
    assert result["max_drawdown_estimate"] >= 0
    assert "not a profit forecast" in result["caveat"].lower()


def test_backtest_engine_returns_not_available_for_wait_signal() -> None:
    result = run_lightweight_backtest(
        _trend_frame(direction="up"),
        signal_rules={"signal": "WAIT"},
        timeframe="H1",
        symbol="BTCUSD",
    )

    assert result["status"] == "not_available"
    assert result["estimated_win_rate"] is None
    assert result["caveat"]


def test_backtest_engine_returns_not_available_for_short_data() -> None:
    result = run_lightweight_backtest(
        _trend_frame(direction="up", points=20),
        signal_rules={"signal": "BUY"},
        timeframe="H1",
        symbol="BTCUSD",
    )

    assert result["status"] == "not_available"
    assert result["sample_size"] == 0


def _trend_frame(direction: str, points: int = 100) -> pd.DataFrame:
    rows = []
    for index in range(points):
        move = index * 0.2 if direction == "up" else -index * 0.2
        close = 100.0 + move
        rows.append(
            {
                "Open": close - 0.1,
                "High": close + 0.3,
                "Low": close - 0.3,
                "Close": close,
                "Volume": 1000.0 + index,
            }
        )
    return pd.DataFrame(rows)
