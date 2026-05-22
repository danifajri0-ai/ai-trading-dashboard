from __future__ import annotations

from domain.market_context_engine import build_market_context_lite


def test_build_market_context_lite_detects_bullish_normal_regime() -> None:
    context = build_market_context_lite(
        price=110,
        ema_20=105,
        ema_50=100,
        ema_200=95,
        current_atr=1.0,
        average_atr=1.0,
    )

    assert context["status"] == "available"
    assert context["regime_label"] == "bullish_trend"
    assert context["volatility_state"] == "normal_volatility"
    assert context["trend_state"] == "bullish_trend"
    assert context["atr_ratio"] == 1.0
    assert context["ma_spread_ema200"] > 0
    assert 0 <= context["regime_score"] <= 100
    assert context["warnings"] == []


def test_build_market_context_lite_detects_bearish_high_volatility_regime() -> None:
    context = build_market_context_lite(
        price=90,
        ema_20=95,
        ema_50=100,
        ema_200=105,
        current_atr=3.2,
        average_atr=2.0,
    )

    assert context["status"] == "available"
    assert context["regime_label"] == "bearish_trend_high_volatility"
    assert context["volatility_state"] == "high_volatility"
    assert context["trend_state"] == "bearish_trend"
    assert context["atr_ratio"] == 1.6
    assert any("above 1.5" in warning for warning in context["warnings"])


def test_build_market_context_lite_detects_low_volatility_range() -> None:
    context = build_market_context_lite(
        price=100,
        ema_20=101,
        ema_50=99,
        ema_200=100,
        current_atr=0.7,
        average_atr=1.0,
    )

    assert context["status"] == "available"
    assert context["regime_label"] == "low_volatility_range"
    assert context["volatility_state"] == "low_volatility"
    assert context["trend_state"] == "mixed_or_range"
    assert any("below 0.8" in warning for warning in context["warnings"])
    assert any("mixed or range-bound" in warning for warning in context["warnings"])


def test_build_market_context_lite_returns_unavailable_for_missing_inputs() -> None:
    context = build_market_context_lite(
        price=None,
        ema_20=105,
        ema_50=100,
        ema_200=95,
        current_atr=1.0,
        average_atr=1.0,
    )

    assert context["status"] == "unavailable"
    assert context["reason"] == "required inputs missing"
    assert context["regime_label"] == "unknown"
    assert context["regime_score"] == 0.0
    assert context["warnings"] == ["required inputs missing"]


def test_build_market_context_lite_returns_unavailable_for_invalid_inputs() -> None:
    context = build_market_context_lite(
        price=100,
        ema_20="not-a-number",
        ema_50=100,
        ema_200=95,
        current_atr=1.0,
        average_atr=1.0,
    )

    assert context["status"] == "unavailable"
    assert context["reason"] == "required inputs missing"


def test_build_market_context_lite_handles_zero_average_atr_safely() -> None:
    context = build_market_context_lite(
        price=110,
        ema_20=105,
        ema_50=100,
        ema_200=95,
        current_atr=1.0,
        average_atr=0.0,
    )

    assert context["status"] == "available"
    assert context["atr_ratio"] == 0.0
    assert context["volatility_state"] == "low_volatility"
    assert any("invalid" in warning for warning in context["warnings"])
