from __future__ import annotations

from domain.cockpit.evidence_engine import build_evidence_layer


def test_evidence_engine_builds_ui_ready_evidence_groups() -> None:
    result = build_evidence_layer(
        signal_validation={
            "status": "available",
            "validation_score": 78.0,
            "confirmation_reason": "Signal aligns with trend.",
            "contradictions": [],
        },
        confidence={"status": "available", "final_confidence": 76.0},
        data_quality={"status": "available", "score": 94.0, "issues": [], "warnings": []},
        risk_gate={"status": "available", "risk_status": "valid", "reasons": ["Risk gate passed."]},
        legacy_reasons=["Trend is bullish."],
        legacy_warnings=[],
    )

    assert result["status"] == "available"
    assert result["technical_evidence"]
    assert result["risk_evidence"]
    assert result["data_quality_evidence"]
    assert result["contradictions"] == []


def test_evidence_engine_surfaces_contradictions_and_caution_status() -> None:
    result = build_evidence_layer(
        signal_validation={
            "status": "caution",
            "validation_score": 40.0,
            "warning_reason": "Momentum does not confirm.",
            "contradictions": ["BUY signal conflicts with bearish trend/bias."],
        },
        confidence={"status": "caution", "final_confidence": 44.0},
        data_quality={"status": "caution", "score": 60.0, "issues": ["Latest candle is stale."], "warnings": []},
        risk_gate={"status": "available", "risk_status": "caution", "reasons": ["Risk/reward is low."]},
        legacy_reasons=[],
        legacy_warnings=["High risk setup."],
    )

    assert result["status"] == "caution"
    assert result["contradictions"]
    assert any(item["status"] == "caution" for item in result["data_quality_evidence"])
