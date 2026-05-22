from __future__ import annotations

from math import isfinite

from domain.quant import atr_ratio as calculate_atr_ratio
from domain.quant import ma_spread, normalize_score, weighted_score


def build_market_context_lite(
    price: object,
    ema_20: object,
    ema_50: object,
    ema_200: object,
    current_atr: object,
    average_atr: object,
) -> dict[str, object]:
    values = {
        "price": _safe_float(price),
        "ema_20": _safe_float(ema_20),
        "ema_50": _safe_float(ema_50),
        "ema_200": _safe_float(ema_200),
        "current_atr": _safe_float(current_atr),
        "average_atr": _safe_float(average_atr),
    }
    if any(value is None for value in values.values()):
        return _unavailable_context("required inputs missing")

    atr_value = calculate_atr_ratio(values["current_atr"], values["average_atr"])
    spread_ema200 = ma_spread(values["price"], values["ema_200"])
    volatility_state = _volatility_state(atr_value)
    trend_state = _trend_state(
        values["price"],
        values["ema_20"],
        values["ema_50"],
        values["ema_200"],
    )
    regime_label = _regime_label(trend_state, volatility_state)
    warnings = _warnings(volatility_state, trend_state, atr_value)

    return {
        "status": "available",
        "regime_label": regime_label,
        "regime_score": _regime_score(trend_state, volatility_state, atr_value, spread_ema200),
        "volatility_state": volatility_state,
        "trend_state": trend_state,
        "ma_spread_ema200": spread_ema200,
        "atr_ratio": atr_value,
        "warnings": warnings,
    }


def _unavailable_context(reason: str) -> dict[str, object]:
    return {
        "status": "unavailable",
        "reason": reason,
        "regime_label": "unknown",
        "regime_score": 0.0,
        "volatility_state": "unknown",
        "trend_state": "unknown",
        "ma_spread_ema200": 0.0,
        "atr_ratio": 0.0,
        "warnings": [reason],
    }


def _volatility_state(atr_value: float) -> str:
    if atr_value > 1.5:
        return "high_volatility"
    if atr_value < 0.8:
        return "low_volatility"
    return "normal_volatility"


def _trend_state(price: float, ema_20: float, ema_50: float, ema_200: float) -> str:
    if price > ema_20 > ema_50 > ema_200:
        return "bullish_trend"
    if price < ema_20 < ema_50 < ema_200:
        return "bearish_trend"
    return "mixed_or_range"


def _regime_label(trend_state: str, volatility_state: str) -> str:
    if volatility_state == "high_volatility":
        if trend_state in {"bullish_trend", "bearish_trend"}:
            return f"{trend_state}_high_volatility"
        return "volatile_mixed_or_range"
    if trend_state in {"bullish_trend", "bearish_trend"}:
        return trend_state
    if volatility_state == "low_volatility":
        return "low_volatility_range"
    return "mixed_or_range"


def _regime_score(
    trend_state: str,
    volatility_state: str,
    atr_value: float,
    spread_ema200: float,
) -> float:
    trend_score = {
        "bullish_trend": 75.0,
        "bearish_trend": 75.0,
        "mixed_or_range": 40.0,
    }.get(trend_state, 0.0)
    volatility_score = {
        "normal_volatility": 70.0,
        "low_volatility": 55.0,
        "high_volatility": 35.0,
    }.get(volatility_state, 0.0)
    atr_stability_score = 100.0 - normalize_score(abs(atr_value - 1.0), 0.0, 1.0)
    spread_score = normalize_score(abs(spread_ema200), 0.0, 0.05)
    score = weighted_score(
        [
            (trend_score, 0.4),
            (volatility_score, 0.3),
            (atr_stability_score, 0.2),
            (spread_score, 0.1),
        ]
    )
    return round(score, 2)


def _warnings(volatility_state: str, trend_state: str, atr_value: float) -> list[str]:
    warnings: list[str] = []
    if volatility_state == "high_volatility":
        warnings.append("ATR ratio above 1.5; volatility regime is elevated.")
    if volatility_state == "low_volatility":
        warnings.append("ATR ratio below 0.8; volatility regime is compressed.")
    if trend_state == "mixed_or_range":
        warnings.append("Trend alignment is mixed or range-bound.")
    if atr_value <= 0:
        warnings.append("ATR ratio is unavailable or invalid.")
    return warnings


def _safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None
