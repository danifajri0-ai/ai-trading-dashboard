from __future__ import annotations

import pandas as pd


def detect_volatility_regime(atr_percent: float) -> str:
    if atr_percent <= 0:
        return "Unknown"
    if atr_percent <= 2.5:
        return "Calm"
    if atr_percent <= 5:
        return "Normal"
    return "High Volatility"


def classify_market_regime(direction: str, volatility_state: str) -> str:
    if volatility_state == "High Volatility":
        return "VOLATILE"
    if direction in {"BUY", "SELL"}:
        return "TRENDING"
    if volatility_state == "Calm":
        return "RANGING"
    return "TRANSITIONAL"


def detect_liquidity_sweep(data: pd.DataFrame) -> str:
    if len(data) < 12:
        return "Insufficient candles"

    recent = data.tail(12)
    last = recent.iloc[-1]
    previous = recent.iloc[:-1]
    previous_high = float(previous["High"].max())
    previous_low = float(previous["Low"].min())
    last_high = float(last["High"])
    last_low = float(last["Low"])
    last_close = float(last["Close"])

    if last_high > previous_high and last_close < previous_high:
        return "Buy-side liquidity sweep candidate"
    if last_low < previous_low and last_close > previous_low:
        return "Sell-side liquidity sweep candidate"
    return "No fresh sweep detected"


def detect_simple_fvg(data: pd.DataFrame) -> str:
    if len(data) < 3:
        return "Insufficient candles"

    c1 = data.iloc[-3]
    c3 = data.iloc[-1]
    c1_high = float(c1["High"])
    c1_low = float(c1["Low"])
    c3_high = float(c3["High"])
    c3_low = float(c3["Low"])

    if c3_low > c1_high:
        return "Bullish FVG candidate"
    if c3_high < c1_low:
        return "Bearish FVG candidate"
    return "No active 3-candle FVG"


def market_condition_warnings(sentiment_label: str) -> list[str]:
    if sentiment_label == "Negative":
        return ["Sentimen berita cenderung negatif."]
    return []
