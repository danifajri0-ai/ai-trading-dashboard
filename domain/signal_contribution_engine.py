from __future__ import annotations

from math import isfinite

from domain.quant import weighted_score


def build_signal_contribution_lite(
    trend_score: object = None,
    momentum_score: object = None,
    volume_score: object = None,
    volatility_score: object = None,
    structure_score: object = None,
) -> dict[str, object]:
    raw_factors = {
        "trend": trend_score,
        "momentum": momentum_score,
        "volume": volume_score,
        "volatility": volatility_score,
        "structure": structure_score,
    }
    weights = {
        "trend": 0.30,
        "momentum": 0.25,
        "volume": 0.15,
        "volatility": 0.15,
        "structure": 0.15,
    }

    contributions: dict[str, dict[str, float | None]] = {}
    missing_factors: list[str] = []
    scored_items: list[tuple[float, float]] = []

    for factor, raw in raw_factors.items():
        normalized = _normalize_score(raw)
        if normalized is None:
            missing_factors.append(factor)
            contributions[factor] = {
                "score": None,
                "weight": weights[factor],
                "weighted_contribution": None,
            }
            continue
        weighted_value = normalized * weights[factor]
        contributions[factor] = {
            "score": normalized,
            "weight": weights[factor],
            "weighted_contribution": round(weighted_value, 2),
        }
        scored_items.append((normalized, weights[factor]))

    final = round(weighted_score(scored_items), 2) if scored_items else 0.0

    positive_factors = [
        factor
        for factor, details in contributions.items()
        if isinstance(details.get("score"), float) and float(details["score"]) >= 60.0
    ]
    negative_factors = [
        factor
        for factor, details in contributions.items()
        if isinstance(details.get("score"), float) and float(details["score"]) < 40.0
    ]

    return {
        "status": "available",
        "final_score": final,
        "contributions": contributions,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "missing_factors": missing_factors,
    }


def _normalize_score(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(number):
        return None
    return max(0.0, min(100.0, number))
