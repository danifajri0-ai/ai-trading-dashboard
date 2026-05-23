from __future__ import annotations

import pandas as pd

from domain.cockpit.market_structure_engine import analyze_market_structure


def test_market_structure_engine_detects_higher_high_higher_low() -> None:
    result = analyze_market_structure(_structure_frame(direction="up"))

    assert result["status"] in {"available", "caution"}
    assert result["swing_pattern"]["high"] == "HH"
    assert result["swing_pattern"]["low"] == "HL"
    assert result["support"] is not None
    assert result["resistance"] is not None


def test_market_structure_engine_detects_breakout_note() -> None:
    frame = _structure_frame(direction="range")
    previous_high = frame["High"].iloc[:-1].max()
    frame.loc[frame.index[-1], "Close"] = previous_high + 1.0
    frame.loc[frame.index[-1], "High"] = previous_high + 1.3

    result = analyze_market_structure(frame)

    assert result["status"] == "available"
    assert result["breakout_note"] == "Close broke above recent resistance."


def test_market_structure_engine_returns_not_available_for_short_data() -> None:
    result = analyze_market_structure(_structure_frame(points=5))

    assert result["status"] == "not_available"
    assert result["structure"] == "unknown"


def _structure_frame(direction: str = "up", points: int = 40) -> pd.DataFrame:
    rows = []
    for index in range(points):
        if direction == "up":
            close = 100.0 + index * 0.15
        elif direction == "range":
            close = 100.0 + (0.2 if index % 2 == 0 else -0.2)
        else:
            close = 100.0 - index * 0.15
        rows.append(
            {
                "High": close + 0.4,
                "Low": close - 0.4,
                "Close": close,
            }
        )
    return pd.DataFrame(rows)
