from __future__ import annotations

from domain.cockpit.confidence_engine import calculate_final_confidence


def test_confidence_engine_calculates_weighted_confidence_breakdown() -> None:
    result = calculate_final_confidence(
        legacy_confidence=70.0,
        signal_validation={"validation_score": 80.0},
        data_quality={"score": 90.0},
        risk_gate={"risk_status": "valid"},
    )

    assert result["status"] == "available"
    assert 0 <= result["final_confidence"] <= 100
    assert result["final_confidence"] > 70
    assert set(result["breakdown"]) == {
        "legacy_confidence",
        "signal_validation",
        "data_quality",
        "risk_gate",
    }


def test_confidence_engine_returns_caution_when_some_components_missing() -> None:
    result = calculate_final_confidence(
        legacy_confidence=65.0,
        signal_validation=None,
        data_quality={"score": 50.0},
        risk_gate={},
    )

    assert result["status"] == "caution"
    assert result["final_confidence"] > 0
    assert result["notes"]


def test_confidence_engine_returns_not_available_without_scores() -> None:
    result = calculate_final_confidence(
        legacy_confidence=None,
        signal_validation={},
        data_quality={},
        risk_gate={},
    )

    assert result["status"] == "not_available"
    assert result["final_confidence"] == 0.0
