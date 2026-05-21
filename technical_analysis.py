from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import pandas as pd
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange


@dataclass(frozen=True)
class IndicatorSettings:
    ema_fast: int = 20
    ema_slow: int = 50
    rsi_window: int = 14
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
    rsi: float
    atr: float
    atr_percent: float
    distance_to_support: float
    distance_to_resistance: float


@dataclass(frozen=True)
class TrendAnalysis:
    trend: str
    bias: str
    direction: str
    strength: str
    explanation: str


@dataclass(frozen=True)
class RiskPlan:
    direction: str
    entry_area: float | None
    stop_loss: float | None
    take_profit: float | None
    risk: float | None
    reward: float | None
    risk_reward: float | None
    note: str


def add_indicators(data: pd.DataFrame, settings: IndicatorSettings) -> pd.DataFrame:
    if data.empty:
        raise ValueError("Data kosong, indikator tidak dapat dihitung.")

    result = data.copy()
    result["EMA_FAST"] = result["Close"].ewm(span=settings.ema_fast, adjust=False).mean()
    result["EMA_SLOW"] = result["Close"].ewm(span=settings.ema_slow, adjust=False).mean()

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

    result["RSI"] = result["RSI"].ffill().fillna(50.0)
    result["ATR"] = result["ATR"].ffill().fillna(result["High"] - result["Low"])

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
        rsi=_safe_float(data["RSI"].iloc[-1], 50.0),
        atr=atr,
        atr_percent=(atr / latest_close * 100) if latest_close else 0.0,
        distance_to_support=latest_close - support,
        distance_to_resistance=resistance - latest_close,
    )


def analyze_trend(levels: MarketLevels) -> TrendAnalysis:
    if levels.latest_close > levels.ema_fast > levels.ema_slow:
        if levels.rsi >= 72:
            return TrendAnalysis(
                trend="Bullish Trend",
                bias="BUY Bias",
                direction="BUY",
                strength="Caution",
                explanation=(
                    "Harga berada di atas EMA cepat dan EMA lambat, tetapi RSI sudah tinggi. "
                    "Peluang buy lebih sehat jika menunggu pullback."
                ),
            )
        return TrendAnalysis(
            trend="Bullish Trend",
            bias="BUY Bias",
            direction="BUY",
            strength="Strong",
            explanation="Harga berada di atas EMA cepat dan EMA lambat. Momentum bullish masih valid.",
        )

    if levels.latest_close < levels.ema_fast < levels.ema_slow:
        if levels.rsi <= 28:
            return TrendAnalysis(
                trend="Bearish Trend",
                bias="SELL Bias",
                direction="SELL",
                strength="Caution",
                explanation=(
                    "Harga berada di bawah EMA cepat dan EMA lambat, tetapi RSI sudah rendah. "
                    "Peluang sell lebih sehat jika menunggu pullback."
                ),
            )
        return TrendAnalysis(
            trend="Bearish Trend",
            bias="SELL Bias",
            direction="SELL",
            strength="Strong",
            explanation="Harga berada di bawah EMA cepat dan EMA lambat. Momentum bearish masih valid.",
        )

    return TrendAnalysis(
        trend="Sideways / Mixed",
        bias="Wait and See",
        direction="WAIT",
        strength="Weak",
        explanation="EMA belum searah. Market mixed, lebih aman menunggu breakout atau rejection valid.",
    )


def calculate_risk_plan(
    levels: MarketLevels,
    trend: TrendAnalysis,
    settings: IndicatorSettings,
) -> RiskPlan:
    if trend.direction == "WAIT" or levels.atr <= 0:
        return RiskPlan(
            direction="WAIT",
            entry_area=None,
            stop_loss=None,
            take_profit=None,
            risk=None,
            reward=None,
            risk_reward=None,
            note="Belum ada area entry yang cukup valid karena trend belum jelas.",
        )

    if trend.direction == "BUY":
        entry_area = _blend_entry(levels.support, levels.ema_fast, levels.latest_close, "BUY")
        stop_loss = entry_area - levels.atr
        take_profit = entry_area + (levels.atr * settings.risk_reward)
        note = "Buy lebih ideal saat harga pullback ke area support atau EMA cepat."
    else:
        entry_area = _blend_entry(levels.resistance, levels.ema_fast, levels.latest_close, "SELL")
        stop_loss = entry_area + levels.atr
        take_profit = entry_area - (levels.atr * settings.risk_reward)
        note = "Sell lebih ideal saat harga pullback ke area resistance atau EMA cepat."

    risk = abs(entry_area - stop_loss)
    reward = abs(take_profit - entry_area)
    rr = reward / risk if risk else None

    return RiskPlan(
        direction=trend.direction,
        entry_area=entry_area,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk=risk,
        reward=reward,
        risk_reward=rr,
        note=note,
    )


def format_price(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:,.{decimals}f}"


def _blend_entry(reference: float, ema_fast: float, latest_close: float, direction: str) -> float:
    if direction == "BUY":
        candidates = [price for price in (reference, ema_fast) if price <= latest_close]
        if not candidates:
            return min(reference, ema_fast, latest_close)
    else:
        candidates = [price for price in (reference, ema_fast) if price >= latest_close]
        if not candidates:
            return max(reference, ema_fast, latest_close)

    return sum(candidates) / len(candidates)


def _safe_float(value: object, fallback: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return number if isfinite(number) else fallback
