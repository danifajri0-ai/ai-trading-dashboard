from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from services.analysis_service import analyze_market


def test_analyze_market_minimal_ui_contract() -> None:
    result = analyze_market("BTCUSD", "H1")
    payload = _to_payload_dict(result)

    required_top_level = {
        "symbol",
        "timeframe",
        "bias",
        "signal",
        "confidence",
        "risk_level",
        "trade_quality_score",
        "technical_summary",
        "risk_summary",
        "warnings",
    }
    for field_name in required_top_level:
        assert field_name in payload, f"Missing top-level field: {field_name}"

    assert isinstance(payload["technical_summary"], dict)
    assert isinstance(payload["risk_summary"], dict)
    assert isinstance(payload["warnings"], list)

    technical_summary = payload["technical_summary"]
    risk_summary = payload["risk_summary"]

    for field_name in ("ema_fast", "ema_slow", "rsi", "atr", "support", "resistance"):
        assert field_name in technical_summary, f"Missing technical_summary field: {field_name}"

    for field_name in ("risk_level", "entry_area", "stop_loss", "take_profit", "risk_reward", "max_risk_pct"):
        assert field_name in risk_summary, f"Missing risk_summary field: {field_name}"


def _to_payload_dict(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if is_dataclass(result):
        return asdict(result)
    if hasattr(result, "__dict__"):
        return dict(result.__dict__)
    raise AssertionError("analyze_market must return object or dict payload.")
