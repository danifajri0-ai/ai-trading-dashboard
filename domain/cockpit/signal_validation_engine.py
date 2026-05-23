from __future__ import annotations

from math import isfinite
from typing import Any


ENTRY_SIGNALS = {"BUY", "SELL", "BUY_ON_PULLBACK", "SELL_ON_REJECTION"}


def validate_signal_decision(
    signal: object,
    bias: object,
    trend: object = None,
    rsi: object = None,
    atr_percent: object = None,
    distance_to_support: object = None,
    distance_to_resistance: object = None,
    risk_reward: object = None,
    risk_level: object = None,
) -> dict[str, Any]:
    signal_value = str(signal or "").upper()
    if not signal_value:
        return _not_available("Signal is missing.")
    if signal_value == "WAIT":
        return {
            "status": "caution",
            "validation_score": 45.0,
            "valid_signal": False,
            "blocked_reason": None,
            "warning_reason": "Signal is WAIT; no actionable trade signal to validate.",
            "confirmation_reason": None,
            "contradictions": [],
            "components": {},
        }

    components: dict[str, float] = {}
    contradictions = _contradictions(signal_value, bias, trend)
    warning_reason: list[str] = []
    confirmation_reason: list[str] = []
    blocked_reason: list[str] = []

    trend_score = 35.0 if contradictions else 80.0
    components["trend_alignment"] = trend_score
    if contradictions:
        warning_reason.extend(contradictions)
    else:
        confirmation_reason.append("Signal aligns with directional bias/trend.")

    momentum_score = _momentum_score(signal_value, rsi)
    if momentum_score is None:
        warning_reason.append("Momentum input is not available.")
    else:
        components["momentum"] = momentum_score
        if momentum_score >= 65:
            confirmation_reason.append("Momentum supports the signal.")
        elif momentum_score < 45:
            warning_reason.append("Momentum does not strongly confirm the signal.")

    volatility_score = _volatility_score(atr_percent)
    if volatility_score is None:
        warning_reason.append("Volatility input is not available.")
    else:
        components["volatility"] = volatility_score
        if volatility_score < 40:
            warning_reason.append("Volatility is elevated or unstable.")
        else:
            confirmation_reason.append("Volatility is within a tradable range.")

    structure_score = _structure_score(signal_value, distance_to_support, distance_to_resistance)
    if structure_score is None:
        warning_reason.append("Support/resistance distance is not available.")
    else:
        components["sr_distance"] = structure_score
        if structure_score < 45:
            warning_reason.append("Price is too close to the next support/resistance obstacle.")
        else:
            confirmation_reason.append("Support/resistance distance is acceptable.")

    rr_score = _risk_reward_score(risk_reward)
    if rr_score is None:
        warning_reason.append("Risk/reward input is not available.")
    else:
        components["risk_reward"] = rr_score
        if rr_score < 45:
            blocked_reason.append("Risk/reward is below the minimum validation threshold.")
        elif rr_score >= 70:
            confirmation_reason.append("Risk/reward supports the setup.")

    if str(risk_level).lower() == "extreme":
        blocked_reason.append("Risk level is extreme.")
        components["risk_level"] = 15.0
    elif str(risk_level).lower() == "high":
        warning_reason.append("Risk level is high.")
        components["risk_level"] = 45.0
    elif risk_level is not None:
        components["risk_level"] = 75.0

    if not components:
        return _not_available("No validation inputs are available.")

    validation_score = round(sum(components.values()) / len(components), 2)
    valid_signal = signal_value in ENTRY_SIGNALS and validation_score >= 60 and not blocked_reason
    status = "available" if valid_signal and not warning_reason else "caution"

    return {
        "status": status,
        "validation_score": validation_score,
        "valid_signal": valid_signal,
        "blocked_reason": "; ".join(blocked_reason) if blocked_reason else None,
        "warning_reason": "; ".join(warning_reason) if warning_reason else None,
        "confirmation_reason": "; ".join(confirmation_reason) if confirmation_reason else None,
        "contradictions": contradictions,
        "components": components,
    }


def _not_available(reason: str) -> dict[str, Any]:
    return {
        "status": "not_available",
        "validation_score": 0.0,
        "valid_signal": False,
        "blocked_reason": reason,
        "warning_reason": None,
        "confirmation_reason": None,
        "contradictions": [],
        "components": {},
    }


def _contradictions(signal: str, bias: object, trend: object) -> list[str]:
    checks = " ".join(str(value or "").upper() for value in (bias, trend))
    contradictions: list[str] = []
    if signal.startswith("BUY") and ("BEARISH" in checks or "SELL" in checks):
        contradictions.append("BUY signal conflicts with bearish trend/bias.")
    if signal.startswith("SELL") and ("BULLISH" in checks or "BUY" in checks):
        contradictions.append("SELL signal conflicts with bullish trend/bias.")
    return contradictions


def _momentum_score(signal: str, rsi: object) -> float | None:
    value = _safe_float(rsi)
    if value is None:
        return None
    if signal.startswith("BUY"):
        if value >= 80:
            return 35.0
        if value >= 70:
            return 50.0
        if value >= 50:
            return 80.0
        if value >= 40:
            return 55.0
        return 35.0
    if signal.startswith("SELL"):
        if value <= 20:
            return 35.0
        if value <= 30:
            return 50.0
        if value <= 50:
            return 80.0
        if value <= 60:
            return 55.0
        return 35.0
    return 45.0


def _volatility_score(atr_percent: object) -> float | None:
    value = _safe_float(atr_percent)
    if value is None:
        return None
    if value <= 0:
        return 25.0
    if value <= 0.4:
        return 55.0
    if value <= 2.5:
        return 80.0
    if value <= 4.0:
        return 50.0
    return 30.0


def _structure_score(signal: str, distance_to_support: object, distance_to_resistance: object) -> float | None:
    support_distance = _safe_float(distance_to_support)
    resistance_distance = _safe_float(distance_to_resistance)
    if support_distance is None or resistance_distance is None:
        return None
    if signal.startswith("BUY"):
        return _distance_score(resistance_distance)
    if signal.startswith("SELL"):
        return _distance_score(support_distance)
    return 45.0


def _distance_score(distance: float) -> float:
    if distance <= 0:
        return 20.0
    if distance < 0.25:
        return 40.0
    if distance < 0.75:
        return 60.0
    return 80.0


def _risk_reward_score(risk_reward: object) -> float | None:
    value = _safe_float(risk_reward)
    if value is None:
        return None
    if value < 1.0:
        return 20.0
    if value < 1.2:
        return 35.0
    if value < 1.5:
        return 55.0
    if value < 2.0:
        return 70.0
    return 85.0


def _safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None
