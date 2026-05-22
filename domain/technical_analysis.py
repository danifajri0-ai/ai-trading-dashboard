from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import AverageTrueRange


@dataclass(frozen=True)
class IndicatorSettings:
    ema_fast: int = 20
    ema_slow: int = 50
    moving_average_period: int = 50
    rsi_window: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    atr_window: int = 14
    level_window: int = 30
    risk_reward: float = 2.0


@dataclass(frozen=True)
class MarketLevels:
    latest_close: float
    latest_time: object
    highest_price: float
    lowest_price: float
    average_close: float
    support: float
    resistance: float
    ema_fast: float
    ema_slow: float
    moving_average: float
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    atr: float
    atr_percent: float
    distance_to_support: float
    distance_to_resistance: float


def add_indicators(data: pd.DataFrame, settings: IndicatorSettings) -> pd.DataFrame:
    if data.empty:
        raise ValueError("Data kosong, indikator tidak dapat dihitung.")

    result = data.copy()
    result["EMA_FAST"] = result["Close"].ewm(span=settings.ema_fast, adjust=False).mean()
    result["EMA_SLOW"] = result["Close"].ewm(span=settings.ema_slow, adjust=False).mean()
    result["MA"] = result["Close"].rolling(settings.moving_average_period, min_periods=1).mean()

    if len(result) >= settings.rsi_window:
        result["RSI"] = RSIIndicator(close=result["Close"], window=settings.rsi_window).rsi()
    else:
        result["RSI"] = 50.0

    if len(result) >= settings.atr_window:
        atr = AverageTrueRange(
            high=result["High"],
            low=result["Low"],
            close=result["Close"],
            window=settings.atr_window,
        )
        result["ATR"] = atr.average_true_range()
    else:
        result["ATR"] = (result["High"] - result["Low"]).rolling(2, min_periods=1).mean()

    if len(result) >= max(settings.macd_slow, settings.macd_signal):
        macd = MACD(
            close=result["Close"],
            window_slow=settings.macd_slow,
            window_fast=settings.macd_fast,
            window_sign=settings.macd_signal,
        )
        result["MACD"] = macd.macd()
        result["MACD_SIGNAL"] = macd.macd_signal()
        result["MACD_HIST"] = macd.macd_diff()
    else:
        result["MACD"] = 0.0
        result["MACD_SIGNAL"] = 0.0
        result["MACD_HIST"] = 0.0

    result["RSI"] = result["RSI"].ffill().fillna(50.0)
    result["ATR"] = result["ATR"].ffill().fillna(result["High"] - result["Low"])
    result["MACD"] = result["MACD"].ffill().fillna(0.0)
    result["MACD_SIGNAL"] = result["MACD_SIGNAL"].ffill().fillna(0.0)
    result["MACD_HIST"] = result["MACD_HIST"].ffill().fillna(0.0)
    result["MA"] = result["MA"].ffill().fillna(result["Close"])
    return result


def calculate_levels(data: pd.DataFrame, settings: IndicatorSettings) -> MarketLevels:
    if data.empty:
        raise ValueError("Data kosong, level market tidak dapat dihitung.")

    window = min(settings.level_window, len(data))
    recent = data.tail(window)

    latest_close = _safe_float(data["Close"].iloc[-1])
    support = _safe_float(recent["Low"].min())
    resistance = _safe_float(recent["High"].max())
    atr = max(_safe_float(data["ATR"].iloc[-1]), 0.0)

    return MarketLevels(
        latest_close=latest_close,
        latest_time=data["Timestamp"].iloc[-1] if "Timestamp" in data.columns else data.index[-1],
        highest_price=_safe_float(data["High"].max()),
        lowest_price=_safe_float(data["Low"].min()),
        average_close=_safe_float(data["Close"].mean()),
        support=support,
        resistance=resistance,
        ema_fast=_safe_float(data["EMA_FAST"].iloc[-1]),
        ema_slow=_safe_float(data["EMA_SLOW"].iloc[-1]),
        moving_average=_safe_float(data["MA"].iloc[-1]),
        rsi=_safe_float(data["RSI"].iloc[-1], 50.0),
        macd=_safe_float(data["MACD"].iloc[-1], 0.0),
        macd_signal=_safe_float(data["MACD_SIGNAL"].iloc[-1], 0.0),
        macd_histogram=_safe_float(data["MACD_HIST"].iloc[-1], 0.0),
        atr=atr,
        atr_percent=(atr / latest_close * 100) if latest_close else 0.0,
        distance_to_support=latest_close - support,
        distance_to_resistance=resistance - latest_close,
    )


def format_price(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:,.{decimals}f}"


def _safe_float(value: object, fallback: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return number if isfinite(number) else fallback

