from __future__ import annotations

from apps.streamlit_app.ui.risk_panel import _lite_availability_summary, _risk_gate_distribution
from apps.streamlit_app.ui.signal_card import _available_dict as signal_available_dict


def test_signal_card_available_dict_hides_missing_and_unavailable_context() -> None:
    assert signal_available_dict(None) is None
    assert signal_available_dict({"status": "unavailable"}) is None
    assert signal_available_dict({"status": "available", "regime_label": "bullish_trend"}) == {
        "status": "available",
        "regime_label": "bullish_trend",
    }


def test_risk_gate_distribution_summarizes_known_statuses_only() -> None:
    assert _risk_gate_distribution(None) == ""
    assert _risk_gate_distribution([]) == ""
    assert _risk_gate_distribution(["valid", "caution", "blocked", "blocked", "unknown"]) == (
        "Session gate mix: Valid 1 | Caution 1 | Blocked 2"
    )


def test_lite_availability_summary_returns_expected_text() -> None:
    metrics = {
        "BTCUSD:H1": {
            "market_context_total": 5,
            "market_context_unavailable": 1,
            "risk_gate_total": 5,
            "risk_gate_unavailable": 2,
        }
    }
    assert _lite_availability_summary("BTCUSD", "H1", metrics) == (
        "Session unavailable rate: Market Context 20% (1/5) | Risk Gate 40% (2/5)"
    )
