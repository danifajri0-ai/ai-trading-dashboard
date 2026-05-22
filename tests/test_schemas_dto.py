from __future__ import annotations

import pytest

from schemas import AnalysisResult, MarketRegimeResult, RiskResult, SentimentSummary, TechnicalSummary


def _build_result(confidence: float = 50.0, trade_quality_score: float = 60.0, signal: str = "BUY") -> AnalysisResult:
    return AnalysisResult(
        symbol="BTCUSD",
        timeframe="H1",
        bias="BULLISH",
        signal=signal,
        confidence=confidence,
        risk_level="medium",
        trade_quality_score=trade_quality_score,
        reasons=["sample"],
        warnings=["sample warning"],
        technical_summary=TechnicalSummary(
            trend="Bullish",
            ema_fast=100.0,
            ema_slow=98.0,
            rsi=55.0,
            atr=1.2,
            support=97.0,
            resistance=103.0,
        ),
        sentiment_summary=SentimentSummary(sentiment_label="Neutral", sentiment_score=50.0),
        risk_summary=RiskResult(
            risk_level="medium",
            entry_area=100.0,
            stop_loss=98.0,
            take_profit=104.0,
            risk_reward=2.0,
            max_risk_pct=0.03,
        ),
        market_regime=MarketRegimeResult(
            regime="TRENDING",
            volatility_state="Normal",
            liquidity_condition="No fresh sweep detected",
        ),
    )


def test_dto_accepts_valid_ranges_and_signal() -> None:
    result = _build_result(confidence=80.0, trade_quality_score=90.0, signal="BUY_ON_PULLBACK")
    assert 0 <= result.confidence <= 100
    assert 0 <= result.trade_quality_score <= 100
    assert result.market_context_lite is None
    assert result.risk_gate_lite is None


def test_dto_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        _build_result(confidence=101.0)


def test_dto_rejects_invalid_trade_quality_score() -> None:
    with pytest.raises(ValueError):
        _build_result(trade_quality_score=-1.0)


def test_dto_rejects_invalid_signal() -> None:
    with pytest.raises(ValueError):
        _build_result(signal="HOLD")


def test_dto_rejects_invalid_risk_level() -> None:
    with pytest.raises(ValueError):
        AnalysisResult(
            symbol="BTCUSD",
            timeframe="H1",
            bias="BULLISH",
            signal="BUY",
            confidence=50.0,
            risk_level="MEDIUM",
            trade_quality_score=50.0,
            reasons=["sample"],
            warnings=[],
            technical_summary=TechnicalSummary(
                trend="Bullish",
                ema_fast=100.0,
                ema_slow=98.0,
                rsi=55.0,
                atr=1.2,
                support=97.0,
                resistance=103.0,
            ),
            sentiment_summary=SentimentSummary(sentiment_label="Neutral", sentiment_score=50.0),
            risk_summary=RiskResult(
                risk_level="medium",
                entry_area=100.0,
                stop_loss=98.0,
                take_profit=104.0,
                risk_reward=2.0,
                max_risk_pct=0.03,
            ),
            market_regime=MarketRegimeResult(
                regime="TRENDING",
                volatility_state="Normal",
                liquidity_condition="No fresh sweep detected",
            ),
        )
