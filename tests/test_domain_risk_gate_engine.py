from __future__ import annotations

from domain.risk_gate_engine import evaluate_risk_gate


def test_evaluate_risk_gate_returns_valid_when_inputs_pass() -> None:
    result = evaluate_risk_gate(
        signal_score=72,
        rr_ratio=2.0,
        atr_ratio=1.1,
        data_is_fresh=True,
        spread_is_safe=True,
    )

    assert result["status"] == "available"
    assert result["risk_status"] == "valid"
    assert result["adjusted_confidence"] == 72.0
    assert result["reasons"] == ["Risk gate passed."]


def test_evaluate_risk_gate_blocks_when_data_is_not_fresh() -> None:
    result = evaluate_risk_gate(
        signal_score=80,
        rr_ratio=2.0,
        atr_ratio=1.1,
        data_is_fresh=False,
    )

    assert result["status"] == "available"
    assert result["risk_status"] == "blocked"
    assert result["adjusted_confidence"] == 25.0
    assert any("not fresh" in reason for reason in result["reasons"])


def test_evaluate_risk_gate_blocks_when_rr_ratio_is_too_low() -> None:
    result = evaluate_risk_gate(
        signal_score=80,
        rr_ratio=1.1,
        atr_ratio=1.1,
        data_is_fresh=True,
    )

    assert result["risk_status"] == "blocked"
    assert result["adjusted_confidence"] == 25.0
    assert any("below 1.2" in reason for reason in result["reasons"])


def test_evaluate_risk_gate_cautions_when_rr_ratio_is_suboptimal() -> None:
    result = evaluate_risk_gate(
        signal_score=80,
        rr_ratio=1.3,
        atr_ratio=1.1,
        data_is_fresh=True,
    )

    assert result["risk_status"] == "caution"
    assert result["adjusted_confidence"] == 70.0
    assert any("below 1.5" in reason for reason in result["reasons"])


def test_evaluate_risk_gate_cautions_for_high_atr_and_unsafe_spread() -> None:
    result = evaluate_risk_gate(
        signal_score=80,
        rr_ratio=2.0,
        atr_ratio=1.9,
        data_is_fresh=True,
        spread_is_safe=False,
    )

    assert result["risk_status"] == "caution"
    assert result["adjusted_confidence"] == 60.0
    assert any("above 1.8" in reason for reason in result["reasons"])
    assert any("Spread safety" in reason for reason in result["reasons"])


def test_evaluate_risk_gate_cautions_when_signal_score_is_low() -> None:
    result = evaluate_risk_gate(
        signal_score=40,
        rr_ratio=2.0,
        atr_ratio=1.1,
        data_is_fresh=True,
    )

    assert result["risk_status"] == "caution"
    assert result["adjusted_confidence"] == 30.0
    assert any("minimum confidence" in reason for reason in result["reasons"])


def test_evaluate_risk_gate_clamps_adjusted_confidence() -> None:
    high = evaluate_risk_gate(
        signal_score=140,
        rr_ratio=2.0,
        atr_ratio=1.1,
        data_is_fresh=True,
    )
    low = evaluate_risk_gate(
        signal_score=-20,
        rr_ratio=2.0,
        atr_ratio=1.9,
        data_is_fresh=True,
    )

    assert high["adjusted_confidence"] == 100.0
    assert low["adjusted_confidence"] == 0.0


def test_evaluate_risk_gate_returns_unavailable_for_missing_inputs() -> None:
    result = evaluate_risk_gate(
        signal_score=None,
        rr_ratio=2.0,
        atr_ratio=1.1,
        data_is_fresh=True,
    )

    assert result["status"] == "unavailable"
    assert result["reason"] == "required inputs missing"
    assert result["risk_status"] == "blocked"
    assert result["adjusted_confidence"] == 0.0


def test_evaluate_risk_gate_returns_unavailable_for_invalid_bool_inputs() -> None:
    result = evaluate_risk_gate(
        signal_score=80,
        rr_ratio=2.0,
        atr_ratio=1.1,
        data_is_fresh="yes",
    )

    assert result["status"] == "unavailable"
    assert result["reason"] == "required inputs missing"
