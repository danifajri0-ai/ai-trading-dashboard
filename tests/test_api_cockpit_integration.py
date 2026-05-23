from __future__ import annotations

import pandas as pd
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routes import cockpit as cockpit_route
from services.analysis_service import AnalysisService
from services.cockpit_service import CockpitService
from services.market_data_service import MarketDataService


class EmptyMarketDataService(MarketDataService):
    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:  # noqa: ARG002
        return pd.DataFrame(columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])


def test_post_cockpit_analyze_returns_cockpit_contract(monkeypatch) -> None:
    client = TestClient(app)
    service = CockpitService(
        analysis_service=AnalysisService(market_data_service=EmptyMarketDataService()),
        signal_history_path=None,
    )
    monkeypatch.setattr(cockpit_route, "analyze_cockpit_market", service.analyze_cockpit)

    response = client.post(
        "/cockpit/analyze",
        json={"symbol": "BTCUSD", "timeframe": "H1"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["schema_version"] == "cockpit.v1"
    assert payload["symbol"] == "BTCUSD"
    assert payload["timeframe"] == "H1"
    assert payload["feature_flags"]["legacy_analysis_included"] is True
    assert payload["legacy_result"]["symbol"] == "BTCUSD"

    for section in (
        "price_snapshot",
        "market_overview",
        "market_context",
        "signal_decision",
        "confidence_breakdown",
        "evidence_layer",
        "multi_timeframe",
        "regime_analysis",
        "market_structure",
        "risk_plan",
        "risk_gate",
        "data_quality",
        "sentiment_context",
        "backtest_snapshot",
        "validation_notes",
        "ui_sections",
    ):
        assert "status" in payload[section], f"Missing status in {section}"
