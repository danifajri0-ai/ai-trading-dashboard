from __future__ import annotations

from domain.risk_engine import RiskPlan, TrendAnalysis
from domain.signal_engine import build_signal_summary
from domain.technical_analysis import MarketLevels


def _sample_levels() -> MarketLevels:
    return MarketLevels(
        latest_close=100.0,
        latest_time="2026-01-01 00:00",
        highest_price=105.0,
        lowest_price=95.0,
        average_close=100.0,
        support=97.0,
        resistance=103.0,
        ema_fast=101.0,
        ema_slow=99.0,
        moving_average=100.0,
        rsi=55.0,
        macd=0.25,
        macd_signal=0.2,
        macd_histogram=0.05,
        atr=1.2,
        atr_percent=1.2,
        distance_to_support=3.0,
        distance_to_resistance=3.0,
    )


def test_signal_engine_confidence_and_action_valid() -> None:
    levels = _sample_levels()
    trend = TrendAnalysis(
        trend="Bullish Trend",
        bias="BUY Bias",
        direction="BUY",
        strength="Strong",
        explanation="sample",
    )
    risk = RiskPlan(
        direction="BUY",
        entry_area=100.0,
        stop_loss=99.0,
        take_profit=102.0,
        risk=1.0,
        reward=2.0,
        risk_reward=2.0,
        note="sample",
    )
    summary = build_signal_summary(levels, trend, risk)
    assert 0 <= summary.confidence <= 100
    assert summary.action in {"BUY", "SELL", "WAIT"}

