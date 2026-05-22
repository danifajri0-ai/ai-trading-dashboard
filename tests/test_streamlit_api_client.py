from __future__ import annotations

from apps.streamlit_app.client.api_client import _analysis_result_from_dict


def test_analysis_result_from_dict_accepts_legacy_payload_without_lite_fields() -> None:
    payload = {
        "symbol": "BTCUSD",
        "timeframe": "H1",
        "bias": "BULLISH",
        "signal": "BUY",
        "confidence": 70.0,
        "risk_level": "medium",
        "trade_quality_score": 62.0,
        "reasons": ["sample"],
        "warnings": [],
        "technical_summary": {
            "trend": "Bullish",
            "ema_fast": 100.0,
            "ema_slow": 98.0,
            "rsi": 55.0,
            "atr": 1.2,
            "support": 97.0,
            "resistance": 103.0,
            "notes": [],
        },
        "sentiment_summary": {
            "sentiment_label": "Neutral",
            "sentiment_score": 50.0,
            "context": [],
            "source": "legacy",
        },
        "risk_summary": {
            "risk_level": "medium",
            "entry_area": 100.0,
            "stop_loss": 98.0,
            "take_profit": 104.0,
            "risk_reward": 2.0,
            "max_risk_pct": 0.03,
            "notes": [],
        },
        "market_regime": {
            "regime": "TRENDING",
            "volatility_state": "Normal",
            "liquidity_condition": "No fresh sweep detected",
            "notes": [],
        },
    }

    result = _analysis_result_from_dict(payload)

    assert result.symbol == "BTCUSD"
    assert result.market_context_lite is None
    assert result.risk_gate_lite is None
    assert result.data_health_lite is None
    assert result.signal_explanation_lite is None
    assert result.signal_contribution_lite is None
