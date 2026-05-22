from __future__ import annotations

from domain.signal_explanation_engine import build_signal_explanation_lite


def test_signal_explanation_returns_available_with_complete_inputs() -> None:
    result = build_signal_explanation_lite(
        signal="BUY",
        confidence=74,
        market_context_lite={
            "status": "available",
            "regime_label": "bullish_trend",
            "volatility_state": "normal_volatility",
            "trend_state": "bullish_trend",
        },
        risk_gate_lite={
            "status": "available",
            "risk_status": "valid",
            "reasons": ["Risk gate passed."],
        },
        data_health_lite={
            "status": "ok",
            "data_is_fresh": True,
            "missing_candle_detected": False,
            "duplicate_candle_detected": False,
        },
    )

    assert result["status"] == "available"
    assert "Signal BUY" in result["explanation_summary"]
    assert result["supporting_factors"]
    assert result["suggested_action"] == "consider_buy_setup"


def test_signal_explanation_blocked_gate_forces_avoid_trade() -> None:
    result = build_signal_explanation_lite(
        signal="SELL",
        confidence=83,
        market_context_lite={"status": "available", "trend_state": "bearish_trend", "volatility_state": "normal_volatility"},
        risk_gate_lite={
            "status": "available",
            "risk_status": "blocked",
            "reasons": ["Market data is not fresh."],
        },
    )

    assert result["status"] == "available"
    assert result["suggested_action"] == "avoid_trade"
    assert "blocked" in result["explanation_summary"].lower()


def test_signal_explanation_works_when_market_context_unavailable() -> None:
    result = build_signal_explanation_lite(
        signal="WAIT",
        confidence=50,
        market_context_lite={"status": "unavailable", "reason": "required inputs missing"},
        risk_gate_lite={
            "status": "available",
            "risk_status": "caution",
            "reasons": ["Risk/reward ratio is below 1.5."],
        },
    )

    assert result["status"] == "available"
    assert result["suggested_action"] == "wait"
    assert any("context unavailable" in factor.lower() for factor in result["warning_factors"])


def test_signal_explanation_returns_unavailable_when_required_inputs_missing() -> None:
    result = build_signal_explanation_lite(
        signal=None,
        confidence=70,
        market_context_lite={"status": "available"},
        risk_gate_lite={"status": "available", "risk_status": "valid"},
    )

    assert result["status"] == "unavailable"
    assert result["reason"] == "required inputs missing"
    assert result["suggested_action"] == "wait"
