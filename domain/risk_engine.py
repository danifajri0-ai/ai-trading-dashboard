from __future__ import annotations

from dataclasses import dataclass

from domain.technical_analysis import IndicatorSettings, MarketLevels


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


def volatility_regime(atr_percent: float) -> str:
    if atr_percent <= 0:
        return "Unknown"
    if atr_percent <= 2.5:
        return "Low"
    if atr_percent <= 5:
        return "Medium"
    return "High"


def classify_risk_level(atr_percent: float) -> str:
    if atr_percent <= 2.5:
        return "low"
    if atr_percent <= 5:
        return "medium"
    return "high"


def score_trade_quality(confidence: int, risk_level: str) -> int:
    normalized = risk_level.lower()
    penalty = {"low": 0, "medium": 8, "high": 15, "extreme": 20}.get(normalized, 10)
    score = max(0, min(100, confidence - penalty))
    return int(score)


def risk_warnings(risk_level: str) -> list[str]:
    if risk_level in {"high", "extreme"}:
        return ["Volatilitas tinggi, gunakan ukuran posisi lebih kecil."]
    return []


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
