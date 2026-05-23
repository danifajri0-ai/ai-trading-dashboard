from __future__ import annotations

import pandas as pd

from domain.cockpit.data_quality_engine import evaluate_data_quality


def test_data_quality_scores_clean_ohlcv_as_available() -> None:
    frame = _frame(points=80)

    result = evaluate_data_quality(frame, timeframe="H1", current_time="2026-01-04T08:30:00Z")

    assert result["status"] == "available"
    assert result["score"] == 100.0
    assert result["missing_data_detected"] is False
    assert result["invalid_ohlc_detected"] is False
    assert result["volume_issue_detected"] is False


def test_data_quality_detects_missing_stale_invalid_volume_and_insufficient_data() -> None:
    frame = _frame(points=20)
    frame = frame.drop(index=[10]).reset_index(drop=True)
    frame.loc[3, "High"] = frame.loc[3, "Low"] - 1
    frame["Volume"] = 0

    result = evaluate_data_quality(frame, timeframe="H1", current_time="2026-01-05T08:00:00Z")

    assert result["status"] == "caution"
    assert result["score"] < 100
    assert result["missing_data_detected"] is True
    assert result["stale_data_detected"] is True
    assert result["invalid_ohlc_detected"] is True
    assert result["volume_issue_detected"] is True
    assert result["insufficient_candles"] is True


def test_data_quality_returns_not_available_for_missing_dataframe() -> None:
    result = evaluate_data_quality(None, timeframe="H1")

    assert result["status"] == "not_available"
    assert result["score"] == 0.0
    assert result["issues"]


def _frame(points: int) -> pd.DataFrame:
    start = pd.Timestamp("2026-01-01T00:00:00Z")
    rows = []
    for index in range(points):
        close = 100.0 + index * 0.1
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
