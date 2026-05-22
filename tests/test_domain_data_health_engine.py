from __future__ import annotations

from datetime import timedelta

import pandas as pd

from domain.data_health_engine import evaluate_data_health


def test_evaluate_data_health_returns_unavailable_when_inputs_missing() -> None:
    result = evaluate_data_health(candles=None, expected_timeframe="H1", latest_timestamp=None)

    assert result["status"] == "unavailable"
    assert result["reason"] == "required inputs missing"
    assert result["data_is_fresh"] is False


def test_evaluate_data_health_ok_when_data_is_fresh_and_clean() -> None:
    now = pd.Timestamp("2026-05-22T12:00:00+00:00")
    frame = _hourly_frame(now=now, count=8)

    result = evaluate_data_health(
        candles=frame,
        expected_timeframe="H1",
        latest_timestamp=frame["Timestamp"].iloc[-1],
        current_time=now,
    )

    assert result["status"] == "ok"
    assert result["data_is_fresh"] is True
    assert result["missing_candle_detected"] is False
    assert result["duplicate_candle_detected"] is False
    assert result["warnings"] == []


def test_evaluate_data_health_warning_for_stale_data() -> None:
    now = pd.Timestamp("2026-05-22T12:00:00+00:00")
    latest = now - pd.Timedelta(hours=5)

    result = evaluate_data_health(
        candles=None,
        expected_timeframe="H1",
        latest_timestamp=latest,
        current_time=now,
    )

    assert result["status"] == "warning"
    assert result["data_is_fresh"] is False
    assert any("stale" in warning.lower() for warning in result["warnings"])


def test_evaluate_data_health_detects_duplicate_candle() -> None:
    now = pd.Timestamp("2026-05-22T12:00:00+00:00")
    frame = _hourly_frame(now=now, count=6)
    frame.loc[len(frame)] = frame.iloc[-1]

    result = evaluate_data_health(
        candles=frame,
        expected_timeframe="H1",
        current_time=now,
    )

    assert result["status"] == "warning"
    assert result["duplicate_candle_detected"] is True
    assert any("duplicate" in warning.lower() for warning in result["warnings"])


def test_evaluate_data_health_detects_missing_candle_gap() -> None:
    now = pd.Timestamp("2026-05-22T12:00:00+00:00")
    frame = _hourly_frame(now=now, count=8)
    frame.loc[4, "Timestamp"] = frame.loc[4, "Timestamp"] + pd.Timedelta(hours=3)

    result = evaluate_data_health(
        candles=frame,
        expected_timeframe="H1",
        current_time=now,
    )

    assert result["status"] == "warning"
    assert result["missing_candle_detected"] is True
    assert any("missing candle" in warning.lower() for warning in result["warnings"])


def _hourly_frame(now: pd.Timestamp, count: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    start = now - timedelta(hours=count - 1)
    for idx in range(count):
        ts = start + timedelta(hours=idx)
        close = 100.0 + idx
        rows.append(
            {
                "Timestamp": ts,
                "Open": close - 0.2,
                "High": close + 0.2,
                "Low": close - 0.3,
                "Close": close,
                "Volume": 1000 + idx,
            }
        )
    return pd.DataFrame(rows)
