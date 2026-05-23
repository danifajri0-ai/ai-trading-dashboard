from __future__ import annotations

from math import isfinite
from typing import Any

import pandas as pd


TIMEFRAME_ORDER = ("M15", "M30", "H1", "H4", "D1")


def analyze_multi_timeframe(timeframe_inputs: dict[str, object], primary_timeframe: str | None = None) -> dict[str, Any]:
    if not timeframe_inputs:
        return _not_available("No multi-timeframe input is available.", primary_timeframe)

    per_timeframe: dict[str, dict[str, Any]] = {}
    conflict_notes: list[str] = []
    available_biases: list[str] = []

    for timeframe, value in sorted(timeframe_inputs.items(), key=lambda item: _timeframe_rank(item[0])):
        summary = _summarize_timeframe(value)
        per_timeframe[str(timeframe).upper()] = summary
        if summary["status"] != "available":
            conflict_notes.append(f"{timeframe}: {summary['reason']}")
            continue
        available_biases.append(str(summary["bias"]))

    if not available_biases:
        return _not_available("No usable timeframe summary could be derived.", primary_timeframe, per_timeframe)

    bullish = available_biases.count("BULLISH")
    bearish = available_biases.count("BEARISH")
    neutral = available_biases.count("NEUTRAL")
    strongest_count = max(bullish, bearish, neutral)
    alignment_score = round((strongest_count / len(available_biases)) * 100.0, 2)
    dominant_bias = _dominant_bias(bullish, bearish, neutral)

    primary_bias = per_timeframe.get(str(primary_timeframe or "").upper(), {}).get("bias")
    if primary_bias and primary_bias != dominant_bias and dominant_bias != "NEUTRAL":
        conflict_notes.append(f"Primary timeframe bias ({primary_bias}) conflicts with dominant bias ({dominant_bias}).")

    status = "available" if alignment_score >= 70 and not conflict_notes else "caution"
    return {
        "status": status,
        "alignment_score": alignment_score,
        "dominant_bias": dominant_bias,
        "per_timeframe": per_timeframe,
        "conflict_notes": conflict_notes,
        "entry_timing": _entry_timing(alignment_score, dominant_bias, primary_bias),
    }


def _not_available(
    reason: str,
    primary_timeframe: str | None,
    per_timeframe: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "status": "not_available",
        "alignment_score": 0.0,
        "dominant_bias": "UNKNOWN",
        "primary_timeframe": primary_timeframe,
        "per_timeframe": per_timeframe or {},
        "conflict_notes": [reason],
        "entry_timing": "not_available",
    }


def _summarize_timeframe(value: object) -> dict[str, Any]:
    if isinstance(value, pd.DataFrame):
        return _summarize_frame(value)
    if isinstance(value, dict):
        return _summarize_mapping(value)
    return {"status": "not_available", "bias": "UNKNOWN", "reason": "Unsupported timeframe input."}


def _summarize_frame(frame: pd.DataFrame) -> dict[str, Any]:
    if frame is None or frame.empty or "Close" not in frame.columns:
        return {"status": "not_available", "bias": "UNKNOWN", "reason": "OHLCV dataframe is empty or missing Close."}

    close = pd.to_numeric(frame["Close"], errors="coerce").dropna()
    if len(close) < 5:
        return {"status": "not_available", "bias": "UNKNOWN", "reason": "Insufficient candles for timeframe bias."}

    first = _safe_float(close.iloc[0])
    last = _safe_float(close.iloc[-1])
    ema_fast = _safe_float(close.ewm(span=min(20, len(close)), adjust=False).mean().iloc[-1])
    ema_slow = _safe_float(close.ewm(span=min(50, len(close)), adjust=False).mean().iloc[-1])
    if first is None or last is None or ema_fast is None or ema_slow is None:
        return {"status": "not_available", "bias": "UNKNOWN", "reason": "Invalid close values for timeframe bias."}

    move_pct = ((last - first) / first * 100.0) if first else 0.0
    if last > ema_fast >= ema_slow and move_pct > 0.05:
        bias = "BULLISH"
    elif last < ema_fast <= ema_slow and move_pct < -0.05:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    return {
        "status": "available",
        "bias": bias,
        "last_close": round(last, 6),
        "move_pct": round(move_pct, 4),
        "ema_fast": round(ema_fast, 6),
        "ema_slow": round(ema_slow, 6),
    }


def _summarize_mapping(value: dict[str, Any]) -> dict[str, Any]:
    bias = str(value.get("bias") or value.get("trend") or "").upper()
    if bias in {"BUY", "BULLISH", "UP"}:
        resolved = "BULLISH"
    elif bias in {"SELL", "BEARISH", "DOWN"}:
        resolved = "BEARISH"
    elif bias in {"WAIT", "NEUTRAL", "RANGE", "RANGING"}:
        resolved = "NEUTRAL"
    else:
        return {"status": "not_available", "bias": "UNKNOWN", "reason": "Summary input does not include a usable bias."}
    return {"status": "available", "bias": resolved, "raw": dict(value)}


def _dominant_bias(bullish: int, bearish: int, neutral: int) -> str:
    if bullish > bearish and bullish >= neutral:
        return "BULLISH"
    if bearish > bullish and bearish >= neutral:
        return "BEARISH"
    if neutral > bullish and neutral > bearish:
        return "NEUTRAL"
    return "MIXED"


def _entry_timing(alignment_score: float, dominant_bias: str, primary_bias: object) -> str:
    if dominant_bias in {"UNKNOWN", "MIXED"}:
        return "wait_for_alignment"
    if alignment_score >= 80 and (primary_bias in {dominant_bias, None}):
        return "trend_following_allowed"
    if alignment_score >= 60:
        return "wait_for_pullback_or_confirmation"
    return "avoid_entry_until_timeframes_align"


def _timeframe_rank(timeframe: str) -> int:
    normalized = str(timeframe).upper()
    return TIMEFRAME_ORDER.index(normalized) if normalized in TIMEFRAME_ORDER else len(TIMEFRAME_ORDER)


def _safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None
