from __future__ import annotations

from domain.risk_engine import analyze_trend, calculate_risk_plan
from domain.technical_analysis import IndicatorSettings, MarketLevels


def _levels_for_buy() -> MarketLevels:
    return MarketLevels(
        latest_close=100.0,
        latest_time="2026-01-01",
        highest_price=110.0,
        lowest_price=90.0,
        average_close=100.0,
        support=96.0,
        resistance=104.0,
        ema_fast=99.0,
        ema_slow=97.0,
        moving_average=98.0,
        rsi=56.0,
        macd=0.3,
        macd_signal=0.2,
        macd_histogram=0.1,
        atr=1.5,
        atr_percent=1.5,
        distance_to_support=4.0,
        distance_to_resistance=4.0,
    )


def test_analyze_trend_and_risk_plan_outputs_valid() -> None:
    levels = _levels_for_buy()
    settings = IndicatorSettings()
    trend = analyze_trend(levels)
    risk = calculate_risk_plan(levels, trend, settings)

    assert trend.direction in {"BUY", "SELL", "WAIT"}
    assert risk.direction in {"BUY", "SELL", "WAIT"}
    if risk.direction != "WAIT":
        assert risk.entry_area is not None
        assert risk.stop_loss is not None
        assert risk.take_profit is not None

