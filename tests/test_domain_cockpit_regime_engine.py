from __future__ import annotations

import pandas as pd

from domain.cockpit.regime_engine import analyze_market_regime


def test_regime_engine_detects_trending_market() -> None:
    result = analyze_market_regime(_trend_frame())

    assert result["status"] == "available"
    assert result["regime"] == "trending"
    assert result["regime_score"] > 70
    assert result["preferred_strategy"] == "trend_following"


def test_regime_engine_detects_breakout_market() -> None:
    frame = _range_frame()
    frame.loc[frame.index[-1], "Close"] = frame["High"].max() + 3.0
    frame.loc[frame.index[-1], "High"] = frame.loc[frame.index[-1], "Close"] + 0.2

    result = analyze_market_regime(frame)

    assert result["status"] == "available"
    assert result["regime"] == "breakout"
    assert result["preferred_strategy"] == "breakout_confirmation"


def test_regime_engine_returns_not_available_for_short_data() -> None:
    result = analyze_market_regime(_range_frame(points=10))

    assert result["status"] == "not_available"
    assert result["regime"] == "unknown"


def _trend_frame(points: int = 80) -> pd.DataFrame:
    rows = []
    for index in range(points):
        close = 100.0 + index * 0.08
        rows.append({"High": close + 0.15, "Low": close - 0.15, "Close": close})
    return pd.DataFrame(rows)


def _range_frame(points: int = 80) -> pd.DataFrame:
    rows = []
    for index in range(points):
        close = 100.0 + (0.2 if index % 2 == 0 else -0.2)
        rows.append({"High": close + 0.2, "Low": close - 0.2, "Close": close})
    return pd.DataFrame(rows)
