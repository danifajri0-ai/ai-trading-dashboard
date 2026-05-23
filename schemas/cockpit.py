from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .dto import AnalysisResult


AvailabilityStatus = Literal["available", "partial", "caution", "not_available"]


@dataclass(frozen=True)
class PriceSnapshot:
    status: AvailabilityStatus
    symbol: str
    timeframe: str
    last_price: float | None = None
    bid: float | None = None
    ask: float | None = None
    price_source: str | None = None
    updated_at: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MarketOverview:
    status: AvailabilityStatus
    bias: str
    signal: str
    risk_level: str
    confidence: float
    trade_quality_score: float
    summary: str
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MarketContext:
    status: AvailabilityStatus
    context: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SignalDecision:
    status: AvailabilityStatus
    action: str
    confidence: float
    bias: str
    validation_score: float | None = None
    valid_signal: bool | None = None
    blocked_reason: str | None = None
    warning_reason: str | None = None
    confirmation_reason: str | None = None
    reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ConfidenceBreakdown:
    status: AvailabilityStatus
    overall_score: float
    components: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceLayer:
    status: AvailabilityStatus
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    technical_notes: list[str] = field(default_factory=list)
    sentiment_notes: list[str] = field(default_factory=list)
    technical_evidence: list[dict[str, Any]] = field(default_factory=list)
    risk_evidence: list[dict[str, Any]] = field(default_factory=list)
    data_quality_evidence: list[dict[str, Any]] = field(default_factory=list)
    contradictions: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class MultiTimeframe:
    status: AvailabilityStatus
    primary_timeframe: str
    alignment_score: float | None = None
    dominant_bias: str | None = None
    per_timeframe_bias: dict[str, str] = field(default_factory=dict)
    conflict_notes: list[str] = field(default_factory=list)
    entry_timing: str | None = None
    timeframes: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RegimeAnalysis:
    status: AvailabilityStatus
    regime: str | None = None
    regime_score: float | None = None
    volatility_state: str | None = None
    liquidity_condition: str | None = None
    preferred_strategy: str | None = None
    risk_adjustment: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MarketStructure:
    status: AvailabilityStatus
    structure: str | None = None
    swing_pattern: dict[str, Any] = field(default_factory=dict)
    support: float | None = None
    resistance: float | None = None
    support_distance_pct: float | None = None
    resistance_distance_pct: float | None = None
    breakout_note: str | None = None
    rejection_note: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RiskPlan:
    status: AvailabilityStatus
    risk_level: str
    entry_area: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    risk_reward: float | None = None
    max_risk_pct: float | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RiskGate:
    status: AvailabilityStatus
    risk_status: str | None = None
    reasons: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DataQuality:
    status: AvailabilityStatus
    score: float | None = None
    freshness_status: str | None = None
    issues: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SentimentContext:
    status: AvailabilityStatus
    sentiment_label: str | None = None
    sentiment_score: float | None = None
    context: list[str] = field(default_factory=list)
    source: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BacktestSnapshot:
    status: AvailabilityStatus
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationNotes:
    status: AvailabilityStatus
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class UiSections:
    status: AvailabilityStatus
    order: list[str] = field(default_factory=list)
    visible: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class FeatureFlags:
    rich_cockpit_schema_v1: bool = True
    legacy_analysis_included: bool = True
    frontend_render_only: bool = True
    experimental_sections_enabled: bool = False


@dataclass(frozen=True)
class CockpitAnalysisResult:
    schema_version: str
    symbol: str
    timeframe: str
    price_snapshot: PriceSnapshot
    market_overview: MarketOverview
    market_context: MarketContext
    signal_decision: SignalDecision
    confidence_breakdown: ConfidenceBreakdown
    evidence_layer: EvidenceLayer
    multi_timeframe: MultiTimeframe
    regime_analysis: RegimeAnalysis
    market_structure: MarketStructure
    risk_plan: RiskPlan
    risk_gate: RiskGate
    data_quality: DataQuality
    sentiment_context: SentimentContext
    backtest_snapshot: BacktestSnapshot
    validation_notes: ValidationNotes
    ui_sections: UiSections
    feature_flags: FeatureFlags
    legacy_result: AnalysisResult
