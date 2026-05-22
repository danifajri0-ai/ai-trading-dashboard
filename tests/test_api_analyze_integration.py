from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routes import analysis as analysis_route
from schemas import AnalysisResult, MarketRegimeResult, RiskResult, SentimentSummary, TechnicalSummary


def test_post_analyze_returns_analysis_result_contract() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={"symbol": "XAUUSD", "timeframe": "H1"},
    )

    assert response.status_code == 200
    payload = response.json()

    required_fields = {
        "symbol",
        "timeframe",
        "bias",
        "signal",
        "confidence",
        "risk_level",
        "trade_quality_score",
        "reasons",
        "warnings",
    }
    assert required_fields.issubset(payload.keys())
    assert "market_context_lite" in payload
    assert "risk_gate_lite" in payload
    assert "data_health_lite" in payload
    assert "signal_explanation_lite" in payload
    assert "signal_contribution_lite" in payload

    assert payload["symbol"] == "XAUUSD"
    assert payload["timeframe"] == "H1"

    assert 0 <= payload["confidence"] <= 100
    assert 0 <= payload["trade_quality_score"] <= 100

    assert payload["risk_level"] in {"low", "medium", "high", "extreme"}
    assert payload["signal"] in {
        "BUY",
        "SELL",
        "WAIT",
        "BUY_ON_PULLBACK",
        "SELL_ON_REJECTION",
        "AVOID_HIGH_RISK",
    }
    assert isinstance(payload["market_context_lite"], dict)
    assert isinstance(payload["risk_gate_lite"], dict)
    assert isinstance(payload["data_health_lite"], dict)
    assert isinstance(payload["signal_explanation_lite"], dict)
    assert isinstance(payload["signal_contribution_lite"], dict)
    assert "status" in payload["market_context_lite"]
    assert "status" in payload["risk_gate_lite"]
    assert "status" in payload["data_health_lite"]
    assert "status" in payload["signal_explanation_lite"]
    assert "status" in payload["signal_contribution_lite"]


def test_post_analyze_supports_explicit_unavailable_lite_fields(monkeypatch) -> None:
    client = TestClient(app)
    fake_result = _build_fake_result(
        market_context_lite={"status": "unavailable", "reason": "required inputs missing"},
        risk_gate_lite={"status": "unavailable", "reason": "required inputs missing"},
        data_health_lite={"status": "unavailable", "reason": "required inputs missing"},
        signal_explanation_lite={"status": "unavailable", "reason": "required inputs missing"},
        signal_contribution_lite={"status": "unavailable", "reason": "required inputs missing"},
    )
    monkeypatch.setattr(analysis_route, "analyze_market", lambda symbol, timeframe: fake_result)

    response = client.post("/analyze", json={"symbol": "BTCUSD", "timeframe": "H1"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["market_context_lite"]["status"] == "unavailable"
    assert payload["risk_gate_lite"]["status"] == "unavailable"
    assert payload["data_health_lite"]["status"] == "unavailable"
    assert payload["signal_explanation_lite"]["status"] == "unavailable"
    assert payload["signal_contribution_lite"]["status"] == "unavailable"
    assert payload["signal"] == "BUY"


def test_post_analyze_supports_explicit_available_lite_fields(monkeypatch) -> None:
    client = TestClient(app)
    fake_result = _build_fake_result(
        market_context_lite={
            "status": "available",
            "regime_label": "bullish_trend",
            "volatility_state": "normal_volatility",
            "trend_state": "bullish_trend",
        },
        risk_gate_lite={
            "status": "available",
            "risk_status": "valid",
            "reasons": ["Risk gate passed."],
            "adjusted_confidence": 77.0,
        },
        data_health_lite={
            "status": "ok",
            "data_is_fresh": True,
            "missing_candle_detected": False,
            "duplicate_candle_detected": False,
            "last_candle_time": "2026-01-01T00:00:00+00:00",
            "warnings": [],
        },
        signal_explanation_lite={
            "status": "available",
            "explanation_summary": "Signal BUY with confidence 77.0%.",
            "supporting_factors": ["Risk gate validation passed."],
            "warning_factors": [],
            "suggested_action": "consider_buy_setup",
        },
        signal_contribution_lite={
            "status": "available",
            "final_score": 66.0,
            "contributions": {},
            "positive_factors": ["trend"],
            "negative_factors": [],
            "missing_factors": [],
        },
    )
    monkeypatch.setattr(analysis_route, "analyze_market", lambda symbol, timeframe: fake_result)

    response = client.post("/analyze", json={"symbol": "BTCUSD", "timeframe": "H1"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["market_context_lite"]["status"] == "available"
    assert payload["risk_gate_lite"]["status"] == "available"
    assert payload["risk_gate_lite"]["risk_status"] == "valid"
    assert payload["data_health_lite"]["status"] == "ok"
    assert payload["signal_explanation_lite"]["status"] == "available"
    assert payload["signal_contribution_lite"]["status"] == "available"
    assert payload["confidence"] == 77.0


def _build_fake_result(
    market_context_lite: dict,
    risk_gate_lite: dict,
    data_health_lite: dict,
    signal_explanation_lite: dict,
    signal_contribution_lite: dict,
) -> AnalysisResult:
    return AnalysisResult(
        symbol="BTCUSD",
        timeframe="H1",
        bias="BULLISH",
        signal="BUY",
        confidence=77.0,
        risk_level="medium",
        trade_quality_score=65.0,
        reasons=["sample"],
        warnings=[],
        technical_summary=TechnicalSummary(
            trend="Bullish",
            ema_fast=100.0,
            ema_slow=99.0,
            rsi=55.0,
            atr=1.2,
            support=98.0,
            resistance=103.0,
            notes=[],
        ),
        sentiment_summary=SentimentSummary(
            sentiment_label="Neutral",
            sentiment_score=50.0,
            context=[],
            source="test",
        ),
        risk_summary=RiskResult(
            risk_level="medium",
            entry_area=100.0,
            stop_loss=99.0,
            take_profit=102.0,
            risk_reward=2.0,
            max_risk_pct=0.03,
            notes=[],
        ),
        market_regime=MarketRegimeResult(
            regime="TRENDING",
            volatility_state="Normal",
            liquidity_condition="No fresh sweep detected",
            notes=[],
        ),
        market_context_lite=dict(market_context_lite),
        risk_gate_lite=dict(risk_gate_lite),
        data_health_lite=dict(data_health_lite),
        signal_explanation_lite=dict(signal_explanation_lite),
        signal_contribution_lite=dict(signal_contribution_lite),
    )
