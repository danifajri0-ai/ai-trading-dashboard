from __future__ import annotations

from domain.quant import atr_ratio, ma_spread, normalize_score, robust_zscore, weighted_score


def test_robust_zscore_returns_clipped_score() -> None:
    assert robust_zscore(16, 10, 2) == 3.0
    assert robust_zscore(4, 10, 2) == -3.0
    assert robust_zscore(13, 10, 2) == 1.5


def test_robust_zscore_handles_invalid_inputs_safely() -> None:
    assert robust_zscore(None, 10, 2) == 0.0
    assert robust_zscore(10, None, 2) == 0.0
    assert robust_zscore(10, 10, 0) == 0.0
    assert robust_zscore(float("nan"), 10, 2) == 0.0
    assert robust_zscore(12, 10, 1, clip_min=2, clip_max=-2) == 2.0


def test_atr_ratio_handles_normal_and_invalid_inputs() -> None:
    assert atr_ratio(3, 2) == 1.5
    assert atr_ratio(None, 2) == 0.0
    assert atr_ratio(2, 0) == 0.0
    assert atr_ratio(-1, 2) == 0.0
    assert atr_ratio(2, "bad") == 0.0


def test_ma_spread_handles_normal_and_invalid_inputs() -> None:
    assert ma_spread(110, 100) == 0.1
    assert ma_spread(90, 100) == -0.1
    assert ma_spread(None, 100) == 0.0
    assert ma_spread(100, 0) == 0.0
    assert ma_spread("bad", 100) == 0.0


def test_normalize_score_clamps_to_zero_to_one_hundred() -> None:
    assert normalize_score(50, 0, 100) == 50.0
    assert normalize_score(-5, 0, 100) == 0.0
    assert normalize_score(120, 0, 100) == 100.0
    assert normalize_score(50, 100, 0) == 50.0


def test_normalize_score_handles_invalid_ranges_safely() -> None:
    assert normalize_score(None, 0, 100) == 0.0
    assert normalize_score(50, 10, 10) == 0.0
    assert normalize_score("bad", 0, 100) == 0.0


def test_weighted_score_accepts_tuples_and_dicts() -> None:
    assert weighted_score([(80, 0.75), (40, 0.25)]) == 70.0
    assert weighted_score([{"score": 60, "weight": 2}, {"value": 30, "weight": 1}]) == 50.0


def test_weighted_score_ignores_invalid_items_safely() -> None:
    assert weighted_score(None) == 0.0
    assert weighted_score([]) == 0.0
    assert weighted_score([(80, 0), (50, -1), ("bad", 2), {"score": 10}]) == 0.0
    assert weighted_score([(100, 1), "bad item", {"value": None, "weight": 1}]) == 100.0
