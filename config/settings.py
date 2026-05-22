from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AppMode = Literal["local_service", "http_api"]


@dataclass(frozen=True)
class IndicatorSettings:
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    atr_period: int = 14
    moving_average_period: int = 50


@dataclass(frozen=True)
class RiskSettings:
    default_risk_per_trade: float = 0.01
    minimum_risk_reward: float = 2.0
    maximum_allowed_risk_level: float = 0.03


@dataclass(frozen=True)
class TradingDashboardSettings:
    mode: AppMode = "local_service"
    supported_symbols: tuple[str, ...] = (
        "XAUUSD",
        "BTCUSD",
        "ETHUSD",
        "SOLUSD",
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "AUDUSD",
        "USDCAD",
    )
    supported_timeframes: tuple[str, ...] = ("M15", "M30", "H1", "H4", "D1")
    indicators: IndicatorSettings = IndicatorSettings()
    risk: RiskSettings = RiskSettings()


SETTINGS = TradingDashboardSettings()

