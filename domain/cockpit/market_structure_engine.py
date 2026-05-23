from __future__ import annotations

from math import isfinite
from typing import Any

import pandas as pd


def analyze_market_structure(candles: object, proximity_threshold_pct: float = 0.5) -> dict[str, Any]:
    frame = _normalize_frame(candles)
    if frame is None or frame.empty:
        return _not_available("OHLCV dataframe is not available.")
    if len(frame) < 20:
        return _not_available("Insufficient candles for market structure analysis.")

    recent = frame.tail(30)
    first_half = recent.iloc[: len(recent) // 2]
    second_half = recent.iloc[len(recent) // 2 :]
    latest_close = _safe_float(frame["Close"].iloc[-1])
    if latest_close is None or latest_close <= 0:
        return _not_available("Invalid latest close for market structure analysis.")

    prev_high = float(first_half["High"].max())
    prev_low = float(first_half["Low"].min())
    recent_high = float(second_half["High"].max())
    recent_low = float(second_half["Low"].min())
    support = float(recent["Low"].min())
    resistance = float(recent["High"].max())

    high_structure = "HH" if recent_high > prev_high else "LH"
    low_structure = "HL" if recent_low > prev_low else "LL"
    structure = f"{high_structure}/{low_structure}"
    support_distance_pct = ((latest_close - support) / latest_close * 100.0)
    resistance_distance_pct = ((resistance - latest_close) / latest_close * 100.0)

    notes: list[str] = []
    if support_distance_pct <= proximity_threshold_pct:
        notes.append("Price is near support.")
    if resistance_distance_pct <= proximity_threshold_pct:
        notes.append("Price is near resistance.")

    breakout_note = None
    rejection_note = None
    previous_resistance = float(frame["High"].iloc[:-1].tail(30).max())
    previous_support = float(frame["Low"].iloc[:-1].tail(30).min())
    last_high = float(frame["High"].iloc[-1])
    last_low = float(frame["Low"].iloc[-1])
    if latest_close > previous_resistance:
        breakout_note = "Close broke above recent resistance."
        notes.append(breakout_note)
    elif latest_close < previous_support:
        breakout_note = "Close broke below recent support."
        notes.append(breakout_note)
    elif last_high > previous_resistance and latest_close <= previous_resistance:
        rejection_note = "Upside breakout attempt rejected below resistance."
        notes.append(rejection_note)
    elif last_low < previous_support and latest_close >= previous_support:
        rejection_note = "Downside breakdown attempt rejected above support."
        notes.append(rejection_note)

    status = "available" if notes else "caution"
    return {
        "status": status,
        "structure": structure,
        "swing_pattern": {
            "high": high_structure,
            "low": low_structure,
        },
        "support": round(support, 6),
        "resistance": round(resistance, 6),
        "support_distance_pct": round(support_distance_pct, 4),
        "resistance_distance_pct": round(resistance_distance_pct, 4),
        "breakout_note": breakout_note,
        "rejection_note": rejection_note,
        "notes": notes or ["Structure is mixed; wait for cleaner confirmation."],
    }


def _not_available(reason: str) -> dict[str, Any]:
    return {
        "status": "not_available",
        "structure": "unknown",
        "swing_pattern": {},
        "support": None,
        "resistance": None,
        "support_distance_pct": None,
        "resistance_distance_pct": None,
        "breakout_note": None,
        "rejection_note": None,
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


def _safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None
