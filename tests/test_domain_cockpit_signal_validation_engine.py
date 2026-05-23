from __future__ import annotations

from domain.cockpit.signal_validation_engine import validate_signal_decision


def test_signal_validation_accepts_confirmed_buy_setup() -> None:
    result = validate_signal_decision(
        signal="BUY",
        bias="BULLISH",
        trend="Bullish",
        rsi=58.0,
        atr_percent=1.2,
        distance_to_support=2.0,
        distance_to_resistance=3.0,
        risk_reward=2.2,
        risk_level="medium",
    )

    assert result["status"] == "available"
    assert result["valid_signal"] is True
    assert result["validation_score"] >= 60
    assert result["blocked_reason"] is None
    assert result["confirmation_reason"]


def test_signal_validation_flags_contradictions_and_bad_risk_reward() -> None:
    result = validate_signal_decision(
        signal="BUY",
        bias="BEARISH",
        trend="Bearish",
        rsi=82.0,
        atr_percent=5.0,
        distance_to_support=2.0,
        distance_to_resistance=0.1,
        risk_reward=0.8,
        risk_level="high",
    )

    assert result["status"] == "caution"
    assert result["valid_signal"] is False
    assert result["blocked_reason"]
    assert result["warning_reason"]
    assert result["contradictions"]


def test_signal_validation_returns_not_available_when_signal_missing() -> None:
    result = validate_signal_decision(signal="", bias="BULLISH")

    assert result["status"] == "not_available"
    assert result["valid_signal"] is False
    assert result["blocked_reason"] == "Signal is missing."
