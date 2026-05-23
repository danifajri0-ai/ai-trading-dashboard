from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


def test_api_analyze_endpoint_preserves_required_contract() -> None:
    client = TestClient(app)

    response = client.post("/analyze", json={"symbol": "BTCUSD", "timeframe": "H1"})

    assert response.status_code == 200
    payload = response.json()
    for field in (
        "symbol",
        "timeframe",
        "bias",
        "signal",
        "confidence",
        "risk_level",
        "trade_quality_score",
        "technical_summary",
        "sentiment_summary",
        "risk_summary",
        "market_regime",
        "market_context_lite",
        "risk_gate_lite",
    ):
        assert field in payload, f"Missing API contract field: {field}"

    assert payload["symbol"] == "BTCUSD"
    assert payload["timeframe"] == "H1"
    assert isinstance(payload["reasons"], list)
    assert isinstance(payload["warnings"], list)
    assert 0 <= payload["confidence"] <= 100

