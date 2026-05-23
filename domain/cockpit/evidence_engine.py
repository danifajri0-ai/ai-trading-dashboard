from __future__ import annotations

from typing import Any


def build_evidence_layer(
    signal_validation: dict[str, Any] | None = None,
    confidence: dict[str, Any] | None = None,
    data_quality: dict[str, Any] | None = None,
    risk_gate: dict[str, Any] | None = None,
    legacy_reasons: list[str] | None = None,
    legacy_warnings: list[str] | None = None,
) -> dict[str, Any]:
    validation = signal_validation or {}
    confidence_result = confidence or {}
    quality = data_quality or {}
    gate = risk_gate or {}

    technical_evidence = _technical_evidence(validation, confidence_result, legacy_reasons or [])
    risk_evidence = _risk_evidence(gate, validation)
    data_quality_evidence = _data_quality_evidence(quality)
    contradictions = _contradictions(validation, legacy_warnings or [])

    status = _resolve_status(technical_evidence, risk_evidence, data_quality_evidence, contradictions)
    return {
        "status": status,
        "technical_evidence": technical_evidence,
        "risk_evidence": risk_evidence,
        "data_quality_evidence": data_quality_evidence,
        "contradictions": contradictions,
    }


def _technical_evidence(
    validation: dict[str, Any],
    confidence: dict[str, Any],
    legacy_reasons: list[str],
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    if validation.get("status") == "not_available":
        evidence.append(_item("Signal validation", "not_available", validation.get("blocked_reason"), None))
    else:
        evidence.append(
            _item(
                "Signal validation",
                validation.get("status", "not_available"),
                validation.get("confirmation_reason") or validation.get("warning_reason"),
                validation.get("validation_score"),
            )
        )

    if confidence:
        evidence.append(
            _item(
                "Final confidence",
                confidence.get("status", "not_available"),
                "Weighted confidence score from available components.",
                confidence.get("final_confidence"),
            )
        )

    for reason in legacy_reasons[:5]:
        evidence.append(_item("Legacy analysis reason", "available", reason, None))
    return evidence


def _risk_evidence(risk_gate: dict[str, Any], validation: dict[str, Any]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    if risk_gate:
        risk_status = risk_gate.get("risk_status")
        detail = "; ".join(str(item) for item in risk_gate.get("reasons", []) if item)
        evidence.append(_item("Risk gate", risk_gate.get("status", "not_available"), detail or risk_status, None))
    if validation.get("blocked_reason"):
        evidence.append(_item("Signal blocker", "caution", validation.get("blocked_reason"), None))
    return evidence


def _data_quality_evidence(data_quality: dict[str, Any]) -> list[dict[str, Any]]:
    if not data_quality:
        return [_item("Data quality", "not_available", "Data quality result is not available.", 0.0)]

    details = []
    details.extend(str(item) for item in data_quality.get("issues", []) if item)
    details.extend(str(item) for item in data_quality.get("warnings", []) if item)
    if not details:
        details.append("OHLCV data passed quality checks.")

    return [
        _item(
            "Data quality",
            data_quality.get("status", "not_available"),
            "; ".join(details),
            data_quality.get("score"),
        )
    ]


def _contradictions(validation: dict[str, Any], legacy_warnings: list[str]) -> list[dict[str, Any]]:
    contradictions = [
        _item("Signal contradiction", "caution", detail, None)
        for detail in validation.get("contradictions", [])
    ]
    for warning in legacy_warnings[:5]:
        contradictions.append(_item("Legacy warning", "caution", warning, None))
    return contradictions


def _resolve_status(*groups: object) -> str:
    flattened = [item for group in groups for item in (group if isinstance(group, list) else [])]
    statuses = {str(item.get("status")) for item in flattened if isinstance(item, dict)}
    if "not_available" in statuses and len(statuses) == 1:
        return "not_available"
    if "caution" in statuses or "not_available" in statuses:
        return "caution"
    return "available"


def _item(label: str, status: object, detail: object, score: object) -> dict[str, Any]:
    return {
        "label": label,
        "status": str(status or "not_available"),
        "detail": str(detail) if detail else None,
        "score": score if isinstance(score, (int, float)) else None,
    }
