from __future__ import annotations

from dataclasses import asdict
from typing import Any

import pandas as pd

from schemas import CockpitAnalysisResult
from services.analysis_service import AnalysisService
from services.cockpit_service import COCKPIT_SCHEMA_VERSION, CockpitService
from services.market_data_service import MarketDataService


class StableMarketDataService(MarketDataService):
    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:  # noqa: ARG002
        return _market_frame()


class FailingSecondaryMarketDataService(MarketDataService):
    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:  # noqa: ARG002
        if timeframe != "H1":
            raise RuntimeError("secondary timeframe unavailable")
        return _market_frame()


class FailingSentimentProvider:
    def get_sentiment_inputs(self, symbol: str, asset_class: str) -> dict[str, Any]:  # noqa: ARG002
        raise RuntimeError("sentiment provider unavailable")


def test_cockpit_service_end_to_end_returns_complete_schema() -> None:
    service = CockpitService(
        analysis_service=AnalysisService(market_data_service=StableMarketDataService()),
        signal_history_path=None,
    )

    result = service.analyze_cockpit("BTCUSD", "H1")
    payload = asdict(result)

    assert isinstance(result, CockpitAnalysisResult)
    assert payload["schema_version"] == COCKPIT_SCHEMA_VERSION
    assert payload["symbol"] == "BTCUSD"
    assert payload["timeframe"] == "H1"
    assert payload["legacy_result"]["symbol"] == "BTCUSD"

    required_sections = {
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
        "feature_flags",
    }
    assert required_sections.issubset(payload)
    for section in required_sections - {"feature_flags"}:
        assert "status" in payload[section], f"Missing status in {section}"


def test_cockpit_service_survives_provider_and_secondary_data_failure() -> None:
    service = CockpitService(
        analysis_service=AnalysisService(market_data_service=FailingSecondaryMarketDataService()),
        signal_history_path=None,
        sentiment_provider=FailingSentimentProvider(),
    )

    result = service.analyze_cockpit("BTCUSD", "H1")

    assert result.price_snapshot.status == "available"
    assert result.multi_timeframe.status in {"available", "caution"}
    assert result.sentiment_context.status in {"not_available", "caution"}
    assert any("provider unavailable" in note.lower() for note in result.sentiment_context.notes)


def _market_frame(points: int = 90) -> pd.DataFrame:
    latest = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=20)
    rows = []
    for index in range(points):
        close = 100.0 + index * 0.08
        rows.append(
            {
                "Timestamp": latest - pd.Timedelta(hours=points - index - 1),
                "Open": close - 0.05,
                "High": close + 0.25,
                "Low": close - 0.25,
                "Close": close,
                "Volume": 1000.0 + index,
            }
        )
    return pd.DataFrame(rows)

