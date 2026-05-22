from __future__ import annotations

from math import isfinite
from typing import Any


def build_signal_explanation_lite(
    signal: object,
    confidence: object,
    market_context_lite: object,
    risk_gate_lite: object,
    data_health_lite: object = None,
) -> dict[str, object]:
    signal_text = _safe_signal(signal)
    score = _safe_float(confidence)
    context = _as_dict(market_context_lite)
    gate = _as_dict(risk_gate_lite)
    health = _as_dict(data_health_lite)

    if signal_text is None or score is None or gate is None:
        return _unavailable("required inputs missing")

    supporting_factors: list[str] = []
    warning_factors: list[str] = []

    gate_status = str(gate.get("risk_status", "")).lower()
    gate_reasons = _as_text_list(gate.get("reasons"))
    if gate_status == "valid":
        supporting_factors.append("Risk gate validation passed.")
    elif gate_status == "caution":
        warning_factors.append("Risk gate flagged caution; execution should be selective.")
    elif gate_status == "blocked":
        warning_factors.append("Risk gate blocked this setup.")
    warning_factors.extend(gate_reasons[:2])

    if context is None or str(context.get("status", "")).lower() == "unavailable":
        warning_factors.append("Market context unavailable; relying on core signal only.")
    else:
        trend_state = str(context.get("trend_state", "")).lower()
        volatility_state = str(context.get("volatility_state", "")).lower()
        regime_label = str(context.get("regime_label", "")).strip()
        if regime_label:
            supporting_factors.append(f"Regime: {regime_label.replace('_', ' ')}.")
        if trend_state == "bullish_trend" and signal_text.startswith("BUY"):
            supporting_factors.append("Trend alignment supports bullish signal.")
        elif trend_state == "bearish_trend" and signal_text.startswith("SELL"):
            supporting_factors.append("Trend alignment supports bearish signal.")
        elif trend_state in {"mixed_or_range", "unknown", ""}:
            warning_factors.append("Trend alignment is mixed.")
        else:
            warning_factors.append("Signal direction conflicts with trend alignment.")

        if volatility_state == "high_volatility":
            warning_factors.append("High volatility regime increases execution risk.")
        elif volatility_state == "normal_volatility":
            supporting_factors.append("Volatility regime is normal.")
        elif volatility_state == "low_volatility":
            warning_factors.append("Low volatility may reduce follow-through.")

    if health is not None and str(health.get("status", "")).lower() != "unavailable":
        if health.get("data_is_fresh") is True:
            supporting_factors.append("Market data freshness is confirmed.")
        else:
            warning_factors.append("Market data is not fresh.")
        if bool(health.get("missing_candle_detected")):
            warning_factors.append("Missing candle detected in dataset.")
        if bool(health.get("duplicate_candle_detected")):
            warning_factors.append("Duplicate candle detected in dataset.")

    supporting_factors = _unique(supporting_factors)[:4]
    warning_factors = _unique(warning_factors)[:4]
    suggested_action = _suggested_action(signal_text, score, gate_status)
    explanation_summary = _summary(signal_text, score, gate_status, supporting_factors, warning_factors)

    return {
        "status": "available",
        "explanation_summary": explanation_summary,
        "supporting_factors": supporting_factors,
        "warning_factors": warning_factors,
        "suggested_action": suggested_action,
    }


def _unavailable(reason: str) -> dict[str, object]:
    return {
        "status": "unavailable",
        "reason": reason,
        "explanation_summary": "Signal explanation is unavailable.",
        "supporting_factors": [],
        "warning_factors": [reason],
        "suggested_action": "wait",
    }


def _summary(
    signal: str,
    confidence: float,
    gate_status: str,
    supporting: list[str],
    warning: list[str],
) -> str:
    base = f"Signal {signal} with confidence {confidence:.1f}%."
    if gate_status == "blocked":
        return f"{base} Risk gate blocked execution."
    if gate_status == "caution":
        return f"{base} Risk gate returned caution."
    if supporting:
        return f"{base} Key support: {supporting[0]}"
    if warning:
        return f"{base} Main caution: {warning[0]}"
    return base


def _suggested_action(signal: str, confidence: float, gate_status: str) -> str:
    if gate_status == "blocked":
        return "avoid_trade"
    if gate_status == "caution":
        return "wait" if confidence < 65 else "reduce_size"
    if signal == "WAIT" or confidence < 45:
        return "wait"
    if signal.startswith("BUY"):
        return "consider_buy_setup"
    if signal.startswith("SELL"):
        return "consider_sell_setup"
    return "wait"


def _safe_signal(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    allowed = {
        "BUY",
        "SELL",
        "WAIT",
        "BUY_ON_PULLBACK",
        "SELL_ON_REJECTION",
        "AVOID_HIGH_RISK",
    }
    if normalized not in allowed:
        return None
    return normalized


def _safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(number):
        return None
    return max(0.0, min(100.0, number))


def _as_dict(value: object) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    return None


def _as_text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            output.append(text)
    return output


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output
