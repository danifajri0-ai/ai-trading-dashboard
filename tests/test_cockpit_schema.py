from __future__ import annotations

from dataclasses import asdict, is_dataclass

import pandas as pd

from schemas import CockpitAnalysisResult
from services.analysis_service import AnalysisService
from services.cockpit_service import COCKPIT_SCHEMA_VERSION, CockpitService
from services.market_data_service import MarketDataService


class EmptyMarketDataService(MarketDataService):
    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:  # noqa: ARG002
        return pd.DataFrame(columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])


class StaticMarketDataService(MarketDataService):
    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:  # noqa: ARG002
        return _market_frame()


class PartialFailureMarketDataService(MarketDataService):
    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:  # noqa: ARG002
        if timeframe in {"M15", "H4"}:
            raise RuntimeError("simulated timeframe failure")
        return _market_frame()


def test_cockpit_schema_can_be_created_from_legacy_analysis() -> None:
    result = _cockpit_result()

    assert isinstance(result, CockpitAnalysisResult)
    assert is_dataclass(result)
    assert result.schema_version == COCKPIT_SCHEMA_VERSION
    assert result.legacy_result.symbol == result.symbol
    assert result.legacy_result.timeframe == result.timeframe


def test_cockpit_schema_exposes_required_sections() -> None:
    payload = asdict(_cockpit_result())
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
        "legacy_result",
    }

    for section in required_sections:
        assert section in payload, f"Missing cockpit section: {section}"

    for section in required_sections - {"feature_flags", "legacy_result"}:
        assert "status" in payload[section], f"Missing status in cockpit section: {section}"


def test_cockpit_service_uses_not_available_for_missing_data_instead_of_fake_values() -> None:
    service = CockpitService(
        analysis_service=AnalysisService(market_data_service=EmptyMarketDataService()),
        signal_history_path=None,
    )
    result = service.analyze_cockpit("BTCUSD", "H1")

    assert result.price_snapshot.status == "not_available"
    assert result.price_snapshot.last_price is None
    assert result.price_snapshot.bid is None
    assert result.price_snapshot.ask is None
    assert result.multi_timeframe.status == "not_available"
    assert result.regime_analysis.status == "not_available"
    assert result.market_structure.status == "not_available"
    assert result.backtest_snapshot.status == "not_available"
    assert result.risk_gate.status == "not_available"
    assert result.data_quality.status == "not_available"


def test_cockpit_service_does_not_crash_and_keeps_legacy_compatibility() -> None:
    result = _cockpit_result()

    assert result.market_overview.signal == result.legacy_result.signal
    assert result.market_overview.confidence == result.legacy_result.confidence
    assert result.risk_plan.risk_level == result.legacy_result.risk_summary.risk_level
    assert result.feature_flags.legacy_analysis_included is True


def test_cockpit_service_includes_evidence_engine_outputs_when_market_data_exists() -> None:
    service = CockpitService(
        analysis_service=AnalysisService(market_data_service=StaticMarketDataService()),
        signal_history_path=None,
    )
    result = service.analyze_cockpit("BTCUSD", "H1")

    assert result.price_snapshot.status == "available"
    assert result.data_quality.score is not None
    assert result.confidence_breakdown.components
    assert result.evidence_layer.technical_evidence
    assert result.evidence_layer.risk_evidence
    assert result.evidence_layer.data_quality_evidence
    assert result.multi_timeframe.alignment_score is not None
    assert result.regime_analysis.regime_score is not None
    assert result.market_structure.structure is not None


def test_cockpit_service_handles_failed_secondary_timeframe_fetches() -> None:
    service = CockpitService(
        analysis_service=AnalysisService(market_data_service=PartialFailureMarketDataService()),
        signal_history_path=None,
    )
    result = service.analyze_cockpit("BTCUSD", "H1")

    assert result.multi_timeframe.status in {"available", "caution"}
    assert "M15" not in result.multi_timeframe.timeframes
    assert result.market_structure.status in {"available", "caution"}


def test_cockpit_service_integrates_backtest_snapshot_and_signal_memory(tmp_path) -> None:
    history_path = tmp_path / "signal_history.jsonl"
    service = CockpitService(
        analysis_service=AnalysisService(market_data_service=StaticMarketDataService()),
        signal_history_path=history_path,
    )

    result = service.analyze_cockpit("BTCUSD", "H1")

    assert history_path.exists()
    assert "backtest" in result.backtest_snapshot.metrics
    assert "performance_memory" in result.backtest_snapshot.metrics
    assert result.backtest_snapshot.metrics["backtest"]["caveat"]
    assert result.backtest_snapshot.metrics["performance_memory"]["caveat"]


def _cockpit_result() -> CockpitAnalysisResult:
    service = CockpitService(
        analysis_service=AnalysisService(market_data_service=EmptyMarketDataService()),
        signal_history_path=None,
    )
    return service.analyze_cockpit("BTCUSD", "H1")


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
