from __future__ import annotations

from math import isfinite


def evaluate_risk_gate(
    signal_score: object,
    rr_ratio: object,
    atr_ratio: object,
    data_is_fresh: object,
    spread_is_safe: object = True,
) -> dict[str, object]:
    score = _safe_float(signal_score)
    rr = _safe_float(rr_ratio)
    atr = _safe_float(atr_ratio)
    fresh = _safe_bool(data_is_fresh)
    spread_safe = _safe_bool(spread_is_safe)

    if score is None or rr is None or atr is None or fresh is None or spread_safe is None:
        return _unavailable_result("required inputs missing")

    reasons: list[str] = []
    blockers: list[str] = []
    cautions: list[str] = []

    if not fresh:
        blockers.append("Market data is not fresh.")
    if rr < 1.2:
        blockers.append("Risk/reward ratio is below 1.2.")
    elif rr < 1.5:
        cautions.append("Risk/reward ratio is below 1.5.")

    if atr > 1.8:
        cautions.append("ATR ratio is above 1.8.")
    if not spread_safe:
        cautions.append("Spread safety check failed.")

    reasons.extend(blockers)
    reasons.extend(cautions)

    if blockers:
        return {
            "status": "available",
            "risk_status": "blocked",
            "reasons": reasons,
            "adjusted_confidence": _clamp_score(min(score, 25.0)),
        }

    if cautions:
        return {
            "status": "available",
            "risk_status": "caution",
            "reasons": reasons,
            "adjusted_confidence": _clamp_score(score - (10.0 * len(cautions))),
        }

    if score < 45:
        return {
            "status": "available",
            "risk_status": "caution",
            "reasons": ["Signal score is below the minimum confidence threshold."],
            "adjusted_confidence": _clamp_score(score - 10.0),
        }

    return {
        "status": "available",
        "risk_status": "valid",
        "reasons": ["Risk gate passed."],
        "adjusted_confidence": _clamp_score(score),
    }


def _unavailable_result(reason: str) -> dict[str, object]:
    return {
        "status": "unavailable",
        "reason": reason,
        "risk_status": "blocked",
        "reasons": [reason],
        "adjusted_confidence": 0.0,
    }


def _safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def _safe_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))
