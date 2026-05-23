from __future__ import annotations

import pandas as pd

from domain.cockpit.multi_timeframe_engine import analyze_multi_timeframe


def test_multi_timeframe_engine_scores_aligned_biases() -> None:
    result = analyze_multi_timeframe(
        {
            "M15": _frame(direction="up"),
            "H1": _frame(direction="up"),
            "H4": _frame(direction="up"),
        },
        primary_timeframe="H1",
    )

    assert result["status"] == "available"
    assert result["alignment_score"] == 100.0
    assert result["dominant_bias"] == "BULLISH"
    assert result["entry_timing"] == "trend_following_allowed"


def test_multi_timeframe_engine_flags_conflicts_without_crashing() -> None:
    result = analyze_multi_timeframe(
        {
            "M15": _frame(direction="down"),
            "H1": _frame(direction="up"),
            "H4": {"bias": "bearish"},
            "D1": object(),
        },
        primary_timeframe="H1",
    )

    assert result["status"] == "caution"
    assert result["alignment_score"] < 100.0
    assert result["conflict_notes"]
    assert result["per_timeframe"]["D1"]["status"] == "not_available"


def test_multi_timeframe_engine_returns_not_available_without_usable_inputs() -> None:
    result = analyze_multi_timeframe({"H1": pd.DataFrame()}, primary_timeframe="H1")

    assert result["status"] == "not_available"
    assert result["alignment_score"] == 0.0
    assert result["entry_timing"] == "not_available"


def _frame(direction: str, points: int = 70) -> pd.DataFrame:
    rows = []
    start = pd.Timestamp("2026-01-01T00:00:00Z")
    for index in range(points):
        delta = index * 0.2 if direction == "up" else -index * 0.2
        close = 100.0 + delta
        rows.append(
            {
                "Timestamp": start + pd.Timedelta(hours=index),
                "Open": close - 0.1,
                "High": close + 0.3,
                "Low": close - 0.3,
                "Close": close,
                "Volume": 1000.0 + index,
            }
        )
    return pd.DataFrame(rows)
