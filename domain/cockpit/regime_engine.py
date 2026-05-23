from __future__ import annotations

from math import isfinite
from typing import Any

import pandas as pd


def analyze_market_regime(candles: object) -> dict[str, Any]:
    frame = _normalize_frame(candles)
    if frame is None or frame.empty:
        return _not_available("OHLCV dataframe is not available.")
    if len(frame) < 30:
        return _not_available("Insufficient candles for regime analysis.")

    close = frame["Close"]
    high = frame["High"]
    low = frame["Low"]
    latest_close = _safe_float(close.iloc[-1])
    first_close = _safe_float(close.iloc[0])
    if latest_close is None or first_close is None or first_close <= 0:
        return _not_available("Invalid close values for regime analysis.")

    atr = _average_true_range(frame).tail(14).mean()
    atr_pct = (float(atr) / latest_close * 100.0) if latest_close else 0.0
    recent = frame.tail(20)
    range_high = float(recent["High"].max())
    range_low = float(recent["Low"].min())
    range_pct = ((range_high - range_low) / latest_close * 100.0) if latest_close else 0.0
    move_pct = ((latest_close - first_close) / first_close * 100.0)
    breakout_up = latest_close > float(frame["High"].iloc[:-1].tail(30).max())
    breakout_down = latest_close < float(frame["Low"].iloc[:-1].tail(30).min())

    if breakout_up or breakout_down:
        regime = "breakout"
        score = 78.0
        preferred_strategy = "breakout_confirmation"
        risk_adjustment = "reduce_size_until_retest_confirms"
    elif atr_pct >= 3.5:
        regime = "volatile"
        score = 45.0
        preferred_strategy = "mean_reversion_or_wait"
        risk_adjustment = "reduce_size_and_widen_invalidations"
    elif range_pct <= 1.0 and atr_pct <= 0.8:
        regime = "compression"
        score = 60.0
        preferred_strategy = "wait_for_expansion"
        risk_adjustment = "avoid_early_entry"
    elif abs(move_pct) >= 2.0 and range_pct > 1.0:
        regime = "trending"
        score = 82.0
        preferred_strategy = "trend_following"
        risk_adjustment = "normal_risk_if_pullback_valid"
    else:
        regime = "ranging"
        score = 62.0
        preferred_strategy = "range_fade_near_extremes"
        risk_adjustment = "take_profit_faster"

    return {
        "status": "available" if regime in {"trending", "ranging", "breakout"} else "caution",
        "regime": regime,
        "regime_score": round(score, 2),
        "preferred_strategy": preferred_strategy,
        "risk_adjustment": risk_adjustment,
        "notes": [
            f"ATR%={atr_pct:.2f}",
            f"Recent range%={range_pct:.2f}",
            f"Move%={move_pct:.2f}",
        ],
    }


def _not_available(reason: str) -> dict[str, Any]:
    return {
        "status": "not_available",
        "regime": "unknown",
        "regime_score": 0.0,
        "preferred_strategy": "not_available",
        "risk_adjustment": "not_available",
        "notes": [reason],
    }


def _normalize_frame(candles: object) -> pd.DataFrame | None:
    if not isinstance(candles, pd.DataFrame):
        return None
    required = ("High", "Low", "Close")
    if any(column not in candles.columns for column in required):
        return None
    frame = candles.copy()
    for column in required:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=list(required)).reset_index(drop=True)
    return frame


def _average_true_range(frame: pd.DataFrame) -> pd.Series:
    previous_close = frame["Close"].shift(1)
    tr = pd.concat(
        [
            frame["High"] - frame["Low"],
            (frame["High"] - previous_close).abs(),
            (frame["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(14, min_periods=1).mean()


def _safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None
