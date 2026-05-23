from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


def build_ai_reasoning_context(cockpit_result: object) -> dict[str, Any]:
    payload = _to_dict(cockpit_result)
    return {
        "symbol": payload.get("symbol"),
        "timeframe": payload.get("timeframe"),
        "market_overview": payload.get("market_overview", {}),
        "signal_decision": payload.get("signal_decision", {}),
        "risk_plan": payload.get("risk_plan", {}),
        "risk_gate": payload.get("risk_gate", {}),
        "data_quality": payload.get("data_quality", {}),
        "multi_timeframe": payload.get("multi_timeframe", {}),
        "regime_analysis": payload.get("regime_analysis", {}),
        "market_structure": payload.get("market_structure", {}),
        "sentiment_context": payload.get("sentiment_context", {}),
        "backtest_snapshot": payload.get("backtest_snapshot", {}),
        "evidence_layer": payload.get("evidence_layer", {}),
        "instruction": (
            "Explain the trading setup defensively using only provided schema fields. "
            "Do not claim certainty or guaranteed profit."
        ),
    }


def build_template_reasoning(context: dict[str, Any]) -> dict[str, Any]:
    overview = _as_dict(context.get("market_overview"))
    signal = _as_dict(context.get("signal_decision"))
    risk_gate = _as_dict(context.get("risk_gate"))
    data_quality = _as_dict(context.get("data_quality"))
    regime = _as_dict(context.get("regime_analysis"))

    summary = (
        f"{context.get('symbol', '-')}/{context.get('timeframe', '-')}: "
        f"signal {overview.get('signal', signal.get('action', '-'))}, "
        f"bias {overview.get('bias', '-')}, "
        f"risk gate {risk_gate.get('risk_status', risk_gate.get('status', '-'))}."
    )
    caveats = [
        "LLM mode is disabled; this is deterministic template reasoning.",
        "Use this as explanatory support only, not as financial advice.",
    ]
    if data_quality.get("status") in {"caution", "not_available"}:
        caveats.append("Data quality is limited; confidence should be reduced.")
    if regime.get("status") == "not_available":
        caveats.append("Regime analysis is not available.")

    return {
        "status": "available",
        "mode": "disabled",
        "summary": summary,
        "caveats": caveats,
        "reasoning_points": [
            f"Signal validation: {signal.get('status', 'not_available')}",
            f"Risk level: {overview.get('risk_level', '-')}",
            f"Regime: {regime.get('regime', '-')}",
            f"Data quality: {data_quality.get('status', 'not_available')}",
        ],
    }


def _to_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value):
        return asdict(value)
    return {}


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
