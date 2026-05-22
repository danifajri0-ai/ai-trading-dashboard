from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from math import isfinite
from typing import Any


def robust_zscore(
    value: object,
    median: object,
    mad: object,
    clip_min: float = -3,
    clip_max: float = 3,
) -> float:
    value_number = _safe_float(value)
    median_number = _safe_float(median)
    mad_number = _safe_float(mad)
    if value_number is None or median_number is None or mad_number is None or mad_number <= 0:
        return 0.0

    lower, upper = _safe_clip_bounds(clip_min, clip_max)
    score = (value_number - median_number) / mad_number
    return min(max(score, lower), upper)


def atr_ratio(current_atr: object, average_atr: object) -> float:
    current = _safe_float(current_atr)
    average = _safe_float(average_atr)
    if current is None or average is None or current < 0 or average <= 0:
        return 0.0
    return current / average


def ma_spread(price: object, moving_average: object) -> float:
    price_number = _safe_float(price)
    ma_number = _safe_float(moving_average)
    if price_number is None or ma_number is None or ma_number == 0:
        return 0.0
    return (price_number - ma_number) / abs(ma_number)


def normalize_score(value: object, min_value: object, max_value: object) -> float:
    value_number = _safe_float(value)
    min_number = _safe_float(min_value)
    max_number = _safe_float(max_value)
    if value_number is None or min_number is None or max_number is None:
        return 0.0
    if min_number == max_number:
        return 0.0

    lower = min(min_number, max_number)
    upper = max(min_number, max_number)
    normalized = (value_number - lower) / (upper - lower) * 100
    return min(max(normalized, 0.0), 100.0)


def weighted_score(items: Iterable[object] | None) -> float:
    if items is None:
        return 0.0

    weighted_total = 0.0
    total_weight = 0.0
    for item in items:
        value, weight = _value_and_weight(item)
        if value is None or weight is None or weight <= 0:
            continue
        weighted_total += value * weight
        total_weight += weight

    if total_weight <= 0:
        return 0.0
    return weighted_total / total_weight


def _value_and_weight(item: object) -> tuple[float | None, float | None]:
    if isinstance(item, Mapping):
        value = item.get("value", item.get("score"))
        weight = item.get("weight")
        return _safe_float(value), _safe_float(weight)

    if isinstance(item, Sequence) and not isinstance(item, str) and len(item) >= 2:
        return _safe_float(item[0]), _safe_float(item[1])

    return None, None


def _safe_clip_bounds(clip_min: object, clip_max: object) -> tuple[float, float]:
    lower = _safe_float(clip_min, -3.0)
    upper = _safe_float(clip_max, 3.0)
    if lower is None:
        lower = -3.0
    if upper is None:
        upper = 3.0
    if lower > upper:
        return upper, lower
    return lower, upper


def _safe_float(value: object, fallback: float | None = None) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return number if isfinite(number) else fallback
