from __future__ import annotations

from math import isfinite


def safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def score_grade(value: object) -> str:
    score = safe_float(value)
    if score is None:
        return "Limited data"
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "D"


def delta_from_reference(current: object, reference: object) -> dict[str, str] | None:
    current_value = safe_float(current)
    reference_value = safe_float(reference)
    if current_value is None or reference_value is None:
        return None

    points = current_value - reference_value
    percent = (points / reference_value * 100.0) if reference_value else 0.0
    if abs(points) < 0.000001:
        arrow = "->"
        tone = "neutral"
    elif points > 0:
        arrow = "up"
        tone = "good"
    else:
        arrow = "down"
        tone = "bad"
    return {
        "arrow": arrow,
        "tone": tone,
        "points": f"{points:+,.2f} pts",
        "percent": f"{percent:+,.2f}%",
    }


def readiness_label(value: object) -> str:
    grade = score_grade(value)
    if grade == "A":
        return "High readiness"
    if grade == "B":
        return "Tradable"
    if grade == "C":
        return "Selective"
    if grade == "D":
        return "Low readiness"
    return "Limited data"
