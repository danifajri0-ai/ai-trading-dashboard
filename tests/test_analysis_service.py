from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from schemas import AnalysisResult
from services.analysis_service import AnalysisService, analyze_market
from services.market_data_service import MarketDataService


class EmptyMarketDataService(MarketDataService):
    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:  # noqa: ARG002
        return pd.DataFrame(columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])


class StaticMarketDataService(MarketDataService):
    def __init__(self, frame: pd.DataFrame) -> None:
        super().__init__()
        self._frame = frame

    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:  # noqa: ARG002
        return self._frame.copy()


def test_analyze_market_returns_valid_analysis_result() -> None:
    result = analyze_market("BTCUSD", "H1")
    assert isinstance(result, AnalysisResult)
    assert result.symbol == "BTCUSD"
    assert result.timeframe == "H1"
    assert 0 <= result.confidence <= 100
    assert 0 <= result.trade_quality_score <= 100
    assert isinstance(result.market_context_lite, dict)
    assert isinstance(result.risk_gate_lite, dict)
    assert isinstance(result.data_health_lite, dict)
    assert isinstance(result.signal_explanation_lite, dict)
    assert isinstance(result.signal_contribution_lite, dict)
    assert result.risk_gate_lite.get("status") == "available"


def test_analyze_market_signal_and_risk_level_are_valid() -> None:
    result = analyze_market("BTCUSD", "H1")
    assert result.signal in {
        "BUY",
        "SELL",
        "WAIT",
        "BUY_ON_PULLBACK",
        "SELL_ON_REJECTION",
        "AVOID_HIGH_RISK",
    }
    assert result.risk_level in {"low", "medium", "high", "extreme"}


def test_analyze_market_empty_data_returns_wait_with_warning() -> None:
    service = AnalysisService(market_data_service=EmptyMarketDataService())
    result = service.analyze_market("BTCUSD", "H1")
    assert result.signal == "WAIT"
    assert result.warnings
    assert any("Data kosong" in warning for warning in result.warnings)
    assert result.market_context_lite == {
        "status": "unavailable",
        "reason": "required inputs missing",
    }
    assert result.risk_gate_lite == {
        "status": "unavailable",
        "reason": "required inputs missing",
    }
    assert result.data_health_lite == {
        "status": "unavailable",
        "reason": "required inputs missing",
    }
    assert result.signal_explanation_lite == {
        "status": "unavailable",
        "reason": "required inputs missing",
    }
    assert result.signal_contribution_lite == {
        "status": "unavailable",
        "reason": "required inputs missing",
    }


def test_analyze_market_risk_gate_blocks_stale_market_data() -> None:
    frame = _bullish_frame(latest_age=timedelta(hours=10))
    service = AnalysisService(market_data_service=StaticMarketDataService(frame))

    result = service.analyze_market("BTCUSD", "H1")

    assert result.signal in {
        "BUY",
        "SELL",
        "WAIT",
        "BUY_ON_PULLBACK",
        "SELL_ON_REJECTION",
        "AVOID_HIGH_RISK",
    }
    assert result.risk_gate_lite["status"] == "available"
    assert result.risk_gate_lite["risk_status"] == "blocked"
    assert any("not fresh" in reason for reason in result.risk_gate_lite["reasons"])


def test_analyze_market_risk_gate_cautions_on_unsafe_spread_when_available() -> None:
    frame = _bullish_frame(latest_age=timedelta(minutes=20), bid=99.0, ask=101.0)
    service = AnalysisService(market_data_service=StaticMarketDataService(frame))

    result = service.analyze_market("BTCUSD", "H1")

    assert result.risk_gate_lite["status"] == "available"
    assert any("Spread safety" in reason for reason in result.risk_gate_lite["reasons"])


def test_analyze_market_uses_rr_fallback_when_risk_plan_rr_is_missing() -> None:
    frame = _flat_frame(latest_age=timedelta(minutes=20))
    service = AnalysisService(market_data_service=StaticMarketDataService(frame))

    result = service.analyze_market("BTCUSD", "H1")

    assert result.signal == "WAIT"
    assert result.risk_summary.risk_reward is None
    assert result.risk_gate_lite["status"] == "available"
    assert result.risk_gate_lite["risk_status"] in {"caution", "blocked", "valid"}


def _bullish_frame(
    latest_age: timedelta,
    bid: float | None = None,
    ask: float | None = None,
    points: int = 220,
) -> pd.DataFrame:
    latest = datetime.now(timezone.utc) - latest_age
    rows: list[dict[str, object]] = []
    for index in range(points):
        close = 100.0 + (index * 0.08)
        row: dict[str, object] = {
            "Timestamp": latest - timedelta(hours=points - index - 1),
            "Open": close - 0.05,
            "High": close + 0.2,
            "Low": close - 0.2,
            "Close": close,
            "Volume": 1_000.0 + index,
        }
        if bid is not None and ask is not None:
            row["Bid"] = bid
            row["Ask"] = ask
        rows.append(row)
    return pd.DataFrame(rows)


def _mixed_frame(
    latest_age: timedelta,
    points: int = 220,
) -> pd.DataFrame:
    latest = datetime.now(timezone.utc) - latest_age
    rows: list[dict[str, object]] = []
    for index in range(points):
        close = 100.0 + (0.05 if index % 2 == 0 else -0.05)
        row: dict[str, object] = {
            "Timestamp": latest - timedelta(hours=points - index - 1),
            "Open": close - 0.03,
            "High": close + 0.15,
            "Low": close - 0.15,
            "Close": close,
            "Volume": 900.0 + index,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def _flat_frame(
    latest_age: timedelta,
    points: int = 220,
) -> pd.DataFrame:
    latest = datetime.now(timezone.utc) - latest_age
    rows: list[dict[str, object]] = []
    for index in range(points):
        close = 100.0
        row: dict[str, object] = {
            "Timestamp": latest - timedelta(hours=points - index - 1),
            "Open": close,
            "High": close + 0.1,
            "Low": close - 0.1,
            "Close": close,
            "Volume": 800.0 + index,
        }
        rows.append(row)
    return pd.DataFrame(rows)
