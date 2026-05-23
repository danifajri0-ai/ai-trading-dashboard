from __future__ import annotations

from math import isfinite
from typing import Any


DEFAULT_WEIGHTS = {
    "legacy_confidence": 0.30,
    "signal_validation": 0.30,
    "data_quality": 0.25,
    "risk_gate": 0.15,
}


def calculate_final_confidence(
    legacy_confidence: object,
    signal_validation: dict[str, Any] | None = None,
    data_quality: dict[str, Any] | None = None,
    risk_gate: dict[str, Any] | None = None,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    active_weights = weights or DEFAULT_WEIGHTS
    components = {
        "legacy_confidence": _score_or_none(legacy_confidence),
        "signal_validation": _score_or_none((signal_validation or {}).get("validation_score")),
        "data_quality": _score_or_none((data_quality or {}).get("score")),
        "risk_gate": _risk_gate_score(risk_gate or {}),
    }

    scored_components = {
        name: score
        for name, score in components.items()
        if score is not None and name in active_weights
    }
    if not scored_components:
        return {
            "status": "not_available",
            "final_confidence": 0.0,
            "breakdown": {},
            "notes": ["No confidence inputs are available."],
        }

    total_weight = sum(active_weights[name] for name in scored_components)
    final_score = sum(scored_components[name] * active_weights[name] for name in scored_components) / total_weight
    breakdown = {
        name: {
            "score": round(score, 2),
            "weight": active_weights[name],
            "weighted_score": round(score * active_weights[name], 2),
        }
        for name, score in scored_components.items()
    }
    missing_components = [name for name, score in components.items() if score is None]
    status = "available" if not missing_components else "caution"

    return {
        "status": status,
        "final_confidence": round(_clamp_score(final_score), 2),
        "breakdown": breakdown,
        "notes": [f"Missing confidence component: {name}" for name in missing_components],
    }


def _risk_gate_score(risk_gate: dict[str, Any]) -> float | None:
    if not risk_gate:
        return None
    adjusted = _score_or_none(risk_gate.get("adjusted_confidence"))
    if adjusted is not None:
        return adjusted
    risk_status = str(risk_gate.get("risk_status", "")).lower()
    if risk_status == "valid":
        return 90.0
    if risk_status == "caution":
        return 55.0
    if risk_status == "blocked":
        return 15.0
    return None


def _score_or_none(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(number):
        return None
    return _clamp_score(number)


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))
