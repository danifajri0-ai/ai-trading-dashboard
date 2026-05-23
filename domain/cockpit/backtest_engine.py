from __future__ import annotations

from math import isfinite
from typing import Any

import pandas as pd


DEFAULT_CAVEAT = (
    "Lightweight historical snapshot only. This is not a profit forecast, "
    "does not include fees/slippage/news execution risk, and should only be used as supporting evidence."
)


def run_lightweight_backtest(
    candles: object,
    signal_rules: dict[str, Any] | None = None,
    timeframe: str | None = None,
    symbol: str | None = None,
    lookahead: int = 5,
    min_samples: int = 8,
) -> dict[str, Any]:
    frame = _normalize_frame(candles)
    if frame is None or frame.empty:
        return _not_available("OHLCV dataframe is not available.", symbol, timeframe)
    if len(frame) < 60:
        return _not_available("Insufficient candles for lightweight backtest snapshot.", symbol, timeframe)

    direction = _resolve_direction(signal_rules or {})
    if direction is None:
        return _not_available("Signal direction is not actionable for backtest sampling.", symbol, timeframe)

    samples = _sample_outcomes(frame, direction=direction, lookahead=lookahead)
    if len(samples) < min_samples:
        return _not_available("Not enough matching historical signal samples.", symbol, timeframe, sample_size=len(samples))

    wins = [sample for sample in samples if sample["return_pct"] > 0]
    estimated_win_rate = len(wins) / len(samples) * 100.0
    avg_win = _mean([sample["return_pct"] for sample in wins])
    losses = [abs(sample["return_pct"]) for sample in samples if sample["return_pct"] <= 0]
    avg_loss = _mean(losses)
    avg_rr = (avg_win / avg_loss) if avg_loss > 0 else None
    max_drawdown = _max_drawdown([sample["return_pct"] for sample in samples])

    return {
        "status": "available",
        "symbol": symbol,
        "timeframe": timeframe,
        "sample_size": len(samples),
        "estimated_win_rate": round(estimated_win_rate, 2),
        "avg_rr": round(avg_rr, 2) if avg_rr is not None else None,
        "max_drawdown_estimate": round(max_drawdown, 2),
        "caveat": DEFAULT_CAVEAT,
        "notes": [
            f"Direction sampled: {direction}",
            f"Lookahead candles: {lookahead}",
            "Uses simple MA/momentum conditions; not a full strategy backtest.",
        ],
    }


def _not_available(
    reason: str,
    symbol: str | None,
    timeframe: str | None,
    sample_size: int = 0,
) -> dict[str, Any]:
    return {
        "status": "not_available",
        "symbol": symbol,
        "timeframe": timeframe,
        "sample_size": sample_size,
        "estimated_win_rate": None,
        "avg_rr": None,
        "max_drawdown_estimate": None,
        "caveat": DEFAULT_CAVEAT,
        "notes": [reason],
    }


def _normalize_frame(candles: object) -> pd.DataFrame | None:
    if not isinstance(candles, pd.DataFrame):
        return None
    required = ("Open", "High", "Low", "Close")
    if any(column not in candles.columns for column in required):
        return None
    frame = candles.copy()
    for column in required:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=list(required)).reset_index(drop=True)
    return frame


def _resolve_direction(signal_rules: dict[str, Any]) -> str | None:
    raw = str(signal_rules.get("signal") or signal_rules.get("direction") or "").upper()
    if raw.startswith("BUY"):
        return "BUY"
    if raw.startswith("SELL"):
        return "SELL"
    return None


def _sample_outcomes(frame: pd.DataFrame, direction: str, lookahead: int) -> list[dict[str, float]]:
    close = frame["Close"]
    fast = close.rolling(10, min_periods=10).mean()
    slow = close.rolling(30, min_periods=30).mean()
    samples: list[dict[str, float]] = []

    for index in range(30, len(frame) - lookahead):
        entry = _safe_float(close.iloc[index])
        exit_price = _safe_float(close.iloc[index + lookahead])
        if entry is None or exit_price is None or entry <= 0:
            continue

        fast_value = _safe_float(fast.iloc[index])
        slow_value = _safe_float(slow.iloc[index])
        previous_close = _safe_float(close.iloc[index - 1])
        if fast_value is None or slow_value is None or previous_close is None:
            continue

        momentum_up = close.iloc[index] > previous_close
        momentum_down = close.iloc[index] < previous_close
        buy_match = direction == "BUY" and fast_value >= slow_value and momentum_up
        sell_match = direction == "SELL" and fast_value <= slow_value and momentum_down
        if not buy_match and not sell_match:
            continue

        if direction == "BUY":
            return_pct = (exit_price - entry) / entry * 100.0
        else:
            return_pct = (entry - exit_price) / entry * 100.0
        samples.append({"return_pct": float(return_pct)})
    return samples


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _max_drawdown(returns_pct: list[float]) -> float:
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for return_pct in returns_pct:
        equity *= 1.0 + (return_pct / 100.0)
        peak = max(peak, equity)
        if peak > 0:
            max_drawdown = min(max_drawdown, (equity - peak) / peak * 100.0)
    return abs(max_drawdown)


def _safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None
