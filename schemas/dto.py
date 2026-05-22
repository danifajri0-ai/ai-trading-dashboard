from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

SignalType = Literal[
    "BUY",
    "SELL",
    "WAIT",
    "BUY_ON_PULLBACK",
    "SELL_ON_REJECTION",
    "AVOID_HIGH_RISK",
]

BiasType = Literal["BULLISH", "BEARISH", "NEUTRAL", "MIXED"]
RegimeType = Literal["TRENDING", "RANGING", "VOLATILE", "TRANSITIONAL", "UNKNOWN"]
RiskLevelType = Literal["low", "medium", "high", "extreme"]


@dataclass(frozen=True)
class AnalysisRequest:
    symbol: str
    timeframe: str
    include_sentiment: bool = True
    include_market_regime: bool = True


@dataclass(frozen=True)
class TechnicalSummary:
    trend: str
    ema_fast: float
    ema_slow: float
    rsi: float
    atr: float
    support: float
    resistance: float
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SentimentSummary:
    sentiment_label: str
    sentiment_score: float
    context: list[str] = field(default_factory=list)
    source: str = "internal_context"


@dataclass(frozen=True)
class RiskResult:
    risk_level: RiskLevelType
    entry_area: float | None
    stop_loss: float | None
    take_profit: float | None
    risk_reward: float | None
    max_risk_pct: float
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_risk_level(self.risk_level)


@dataclass(frozen=True)
class MarketRegimeResult:
    regime: RegimeType
    volatility_state: str
    liquidity_condition: str
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnalysisResult:
    symbol: str
    timeframe: str
    bias: str
    signal: SignalType
    confidence: float
    risk_level: RiskLevelType
    trade_quality_score: float
    reasons: list[str]
    warnings: list[str]
    technical_summary: TechnicalSummary
    sentiment_summary: SentimentSummary
    risk_summary: RiskResult
    market_regime: MarketRegimeResult
    market_context_lite: dict[str, Any] | None = None
    risk_gate_lite: dict[str, Any] | None = None
    data_health_lite: dict[str, Any] | None = None
    signal_explanation_lite: dict[str, Any] | None = None
    signal_contribution_lite: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_score_range("confidence", self.confidence)
        _validate_score_range("trade_quality_score", self.trade_quality_score)
        _validate_signal(self.signal)
        _validate_risk_level(self.risk_level)
        if self.risk_level != self.risk_summary.risk_level:
            raise ValueError(
                "risk_level in AnalysisResult must match risk_summary.risk_level. "
                f"Got: {self.risk_level} vs {self.risk_summary.risk_level}"
            )


def _validate_score_range(field_name: str, value: float) -> None:
    if not 0 <= value <= 100:
        raise ValueError(f"{field_name} must be between 0 and 100. Got: {value}")


def _validate_signal(value: str) -> None:
    allowed = {
        "BUY",
        "SELL",
        "WAIT",
        "BUY_ON_PULLBACK",
        "SELL_ON_REJECTION",
        "AVOID_HIGH_RISK",
    }
    if value not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"signal must be one of: {allowed_text}. Got: {value}")


def _validate_risk_level(value: str) -> None:
    allowed = {"low", "medium", "high", "extreme"}
    if value not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"risk_level must be one of: {allowed_text}. Got: {value}")
