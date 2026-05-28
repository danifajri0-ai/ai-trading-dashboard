from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from domain.cockpit import (
    analyze_market_regime,
    analyze_market_structure,
    analyze_multi_timeframe,
    append_signal_snapshot,
    build_evidence_layer,
    calculate_final_confidence,
    evaluate_data_quality,
    read_performance_summary,
    run_lightweight_backtest,
    score_sentiment_inputs,
    validate_signal_decision,
)
from infrastructure.providers import SentimentProvider, build_default_sentiment_provider
from schemas import (
    BacktestSnapshot,
    CockpitAnalysisResult,
    ConfidenceBreakdown,
    DataQuality,
    EvidenceLayer,
    FeatureFlags,
    MarketContext,
    MarketOverview,
    MarketStructure,
    MultiTimeframe,
    PriceSnapshot,
    RegimeAnalysis,
    RiskGate,
    RiskPlan,
    SentimentContext,
    SignalDecision,
    UiSections,
    ValidationNotes,
)
from schemas.dto import AnalysisResult
from services.analysis_service import AnalysisService, analyze_market
from services.market_data_service import MarketDataService


COCKPIT_SCHEMA_VERSION = "cockpit.v1"


@dataclass(frozen=True)
class CockpitService:
    analysis_service: AnalysisService | None = None
    market_data_service: MarketDataService | None = None
    signal_history_path: str | Path | None = "data/cockpit/signal_history.jsonl"
    sentiment_provider: SentimentProvider | None = None

    def analyze_cockpit(self, symbol: str, timeframe: str) -> CockpitAnalysisResult:
        legacy_result = self._analyze_legacy(symbol=symbol, timeframe=timeframe)
        market_frame = self._get_market_frame(legacy_result.symbol, legacy_result.timeframe)
        multi_timeframe_frames = self._get_multi_timeframe_frames(
            legacy_result.symbol,
            legacy_result.timeframe,
            primary_frame=market_frame,
        )
        sentiment_result = self._build_sentiment(legacy_result)
        backtest_result = run_lightweight_backtest(
            market_frame,
            signal_rules={"signal": legacy_result.signal},
            timeframe=legacy_result.timeframe,
            symbol=legacy_result.symbol,
        )
        performance_summary = self._record_and_read_performance(legacy_result, backtest_result)
        return build_cockpit_result(
            legacy_result,
            market_frame=market_frame,
            multi_timeframe_frames=multi_timeframe_frames,
            sentiment_result=sentiment_result,
            backtest_result=backtest_result,
            performance_summary=performance_summary,
        )

    def _analyze_legacy(self, symbol: str, timeframe: str) -> AnalysisResult:
        if self.analysis_service is not None:
            return self.analysis_service.analyze_market(symbol=symbol, timeframe=timeframe)
        return analyze_market(symbol=symbol, timeframe=timeframe)

    def _get_market_frame(self, symbol: str, timeframe: str) -> pd.DataFrame | None:
        service = self.market_data_service
        if service is None and self.analysis_service is not None:
            service = self.analysis_service.market_data_service
        if service is None:
            service = MarketDataService()
        try:
            return service.get_market_data(symbol, timeframe)
        except Exception:
            return None

    def _get_multi_timeframe_frames(
        self,
        symbol: str,
        primary_timeframe: str,
        primary_frame: pd.DataFrame | None,
    ) -> dict[str, pd.DataFrame]:
        service = self.market_data_service
        if service is None and self.analysis_service is not None:
            service = self.analysis_service.market_data_service
        if service is None:
            service = MarketDataService()

        frames: dict[str, pd.DataFrame] = {}
        if isinstance(primary_frame, pd.DataFrame):
            frames[primary_timeframe] = primary_frame

        for timeframe in _supported_timeframes(service, primary_timeframe):
            if timeframe == primary_timeframe and timeframe in frames:
                continue
            try:
                frame = service.get_market_data(symbol, timeframe)
            except Exception:
                continue
            if isinstance(frame, pd.DataFrame):
                frames[timeframe] = frame
        return frames

    def _build_sentiment(self, result: AnalysisResult) -> dict[str, Any]:
        provider = self.sentiment_provider or build_default_sentiment_provider(enable_external_provider=False)
        asset_class = _asset_class_for_symbol(result.symbol)
        try:
            payload = provider.get_sentiment_inputs(symbol=result.symbol, asset_class=asset_class)
        except Exception as exc:
            payload = {
                "status": "not_available",
                "headlines": [],
                "context": [],
                "source": "sentiment_provider",
                "reason": f"Sentiment provider unavailable: {exc}",
            }

        scored = score_sentiment_inputs(
            headlines=[str(item) for item in payload.get("headlines", []) if isinstance(item, str)],
            context=[str(item) for item in payload.get("context", []) if isinstance(item, str)],
        )
        return {
            "status": _merge_sentiment_status(payload.get("status"), scored.get("status")),
            "provider_status": payload.get("status"),
            "scoring_status": scored.get("status"),
            "source": payload.get("source"),
            "reason": payload.get("reason"),
            "sentiment_score": scored.get("sentiment_score"),
            "label": scored.get("label"),
            "key_topics": scored.get("key_topics", []),
            "risk_keywords": scored.get("risk_keywords", []),
            "caveat": scored.get("caveat"),
            "context": payload.get("context", []),
            "headlines": payload.get("headlines", []),
        }

    def _record_and_read_performance(
        self,
        result: AnalysisResult,
        backtest_result: dict[str, Any],
    ) -> dict[str, Any]:
        if self.signal_history_path is None:
            return _performance_memory_unavailable("Signal history persistence is disabled for this service instance.")
        try:
            append_signal_snapshot(
                {
                    "symbol": result.symbol,
                    "timeframe": result.timeframe,
                    "signal": result.signal,
                    "confidence": result.confidence,
                    "risk_level": result.risk_level,
                    "valid_signal": result.signal not in {"WAIT", "AVOID_HIGH_RISK"},
                    "backtest_status": backtest_result.get("status"),
                },
                history_path=self.signal_history_path,
            )
            return read_performance_summary(
                history_path=self.signal_history_path,
                symbol=result.symbol,
                timeframe=result.timeframe,
            )
        except Exception as exc:
            return _performance_memory_unavailable(f"Signal history memory unavailable: {exc}")


def analyze_cockpit_market(symbol: str, timeframe: str) -> CockpitAnalysisResult:
    return _DEFAULT_COCKPIT_SERVICE.analyze_cockpit(symbol=symbol, timeframe=timeframe)


def build_cockpit_result(
    legacy_result: AnalysisResult,
    market_frame: pd.DataFrame | None = None,
    multi_timeframe_frames: dict[str, pd.DataFrame] | None = None,
    sentiment_result: dict[str, Any] | None = None,
    backtest_result: dict[str, Any] | None = None,
    performance_summary: dict[str, Any] | None = None,
) -> CockpitAnalysisResult:
    market_context_lite = _as_dict(legacy_result.market_context_lite)
    risk_gate_lite = _as_dict(legacy_result.risk_gate_lite)
    data_quality_result = evaluate_data_quality(market_frame, legacy_result.timeframe)
    multi_timeframe_result = analyze_multi_timeframe(
        multi_timeframe_frames or {},
        primary_timeframe=legacy_result.timeframe,
    )
    regime_result = analyze_market_regime(market_frame)
    market_structure_result = analyze_market_structure(market_frame)
    signal_validation = _signal_validation(legacy_result, market_frame)
    confidence_result = calculate_final_confidence(
        legacy_confidence=legacy_result.confidence,
        signal_validation=signal_validation,
        data_quality=data_quality_result,
        risk_gate=risk_gate_lite,
    )
    evidence_result = build_evidence_layer(
        signal_validation=signal_validation,
        confidence=confidence_result,
        data_quality=data_quality_result,
        risk_gate=risk_gate_lite,
        legacy_reasons=legacy_result.reasons,
        legacy_warnings=legacy_result.warnings,
    )

    return CockpitAnalysisResult(
        schema_version=COCKPIT_SCHEMA_VERSION,
        symbol=legacy_result.symbol,
        timeframe=legacy_result.timeframe,
        price_snapshot=_price_snapshot(legacy_result, market_frame),
        market_overview=_market_overview(legacy_result),
        market_context=_market_context(market_context_lite),
        signal_decision=_signal_decision(legacy_result, signal_validation),
        confidence_breakdown=_confidence_breakdown(legacy_result, confidence_result),
        evidence_layer=_evidence_layer(legacy_result, evidence_result),
        multi_timeframe=_multi_timeframe(legacy_result, multi_timeframe_result),
        regime_analysis=_regime_analysis(legacy_result, regime_result),
        market_structure=_market_structure(market_structure_result),
        risk_plan=_risk_plan(legacy_result),
        risk_gate=_risk_gate(risk_gate_lite),
        data_quality=_data_quality(data_quality_result),
        sentiment_context=_sentiment_context(legacy_result, sentiment_result),
        backtest_snapshot=_backtest_snapshot(backtest_result, performance_summary),
        validation_notes=_validation_notes(),
        ui_sections=_ui_sections(),
        feature_flags=FeatureFlags(),
        legacy_result=legacy_result,
    )


def _price_snapshot(result: AnalysisResult, market_frame: pd.DataFrame | None) -> PriceSnapshot:
    latest = _latest_market_row(market_frame)
    if latest is not None:
        source = getattr(market_frame, "attrs", {}).get("source") if isinstance(market_frame, pd.DataFrame) else None
        provider_symbol = getattr(market_frame, "attrs", {}).get("provider_symbol") if isinstance(market_frame, pd.DataFrame) else None
        fallback_reason = getattr(market_frame, "attrs", {}).get("fallback_reason") if isinstance(market_frame, pd.DataFrame) else None
        source_label = _price_source_label(source, provider_symbol)
        notes = ["Price snapshot is derived from the latest OHLCV candle."]
        if isinstance(fallback_reason, str) and fallback_reason.strip():
            notes.append(f"Fallback reason: {fallback_reason.strip()}")
        return PriceSnapshot(
            status="available",
            symbol=result.symbol,
            timeframe=result.timeframe,
            last_price=_float_or_none(latest.get("Close")),
            price_source=source_label,
            updated_at=_timestamp_or_none(latest.get("Timestamp")),
            notes=notes,
        )

    return PriceSnapshot(
        status="not_available",
        symbol=result.symbol,
        timeframe=result.timeframe,
        notes=["Legacy AnalysisResult does not expose last tradable price, bid, ask, or timestamp."],
    )


def _market_overview(result: AnalysisResult) -> MarketOverview:
    return MarketOverview(
        status="available",
        bias=result.bias,
        signal=result.signal,
        risk_level=result.risk_level,
        confidence=result.confidence,
        trade_quality_score=result.trade_quality_score,
        summary=f"{result.symbol} {result.timeframe}: {result.signal} with {result.bias} bias.",
        warnings=list(result.warnings),
    )


def _market_context(raw: dict[str, Any]) -> MarketContext:
    return MarketContext(
        status=_availability_from_raw(raw),
        context=raw,
        notes=_notes_from_raw(raw),
    )


def _signal_decision(result: AnalysisResult, validation: dict[str, Any]) -> SignalDecision:
    return SignalDecision(
        status=_availability_from_raw(validation),
        action=result.signal,
        confidence=result.confidence,
        bias=result.bias,
        validation_score=_float_or_none(validation.get("validation_score")),
        valid_signal=validation.get("valid_signal") if isinstance(validation.get("valid_signal"), bool) else None,
        blocked_reason=_string_or_none(validation.get("blocked_reason")),
        warning_reason=_string_or_none(validation.get("warning_reason")),
        confirmation_reason=_string_or_none(validation.get("confirmation_reason")),
        reasons=list(result.reasons),
        notes=["Signal decision is adapted from legacy AnalysisResult."],
    )


def _confidence_breakdown(result: AnalysisResult, raw: dict[str, Any]) -> ConfidenceBreakdown:
    status = _availability_from_raw(raw)
    notes = _notes_from_raw(raw)
    components = raw.get("breakdown") if isinstance(raw.get("breakdown"), dict) else {}
    if status == "not_available":
        notes.append("Only legacy overall confidence is available.")

    return ConfidenceBreakdown(
        status=status,
        overall_score=_float_or_none(raw.get("final_confidence")) or result.confidence,
        components=components,
        notes=notes,
    )


def _evidence_layer(result: AnalysisResult, raw: dict[str, Any]) -> EvidenceLayer:
    return EvidenceLayer(
        status=_availability_from_raw(raw),
        reasons=list(result.reasons),
        warnings=list(result.warnings),
        technical_notes=list(result.technical_summary.notes),
        sentiment_notes=list(result.sentiment_summary.context),
        technical_evidence=_list_of_dicts(raw.get("technical_evidence")),
        risk_evidence=_list_of_dicts(raw.get("risk_evidence")),
        data_quality_evidence=_list_of_dicts(raw.get("data_quality_evidence")),
        contradictions=_list_of_dicts(raw.get("contradictions")),
    )


def _multi_timeframe(result: AnalysisResult, raw: dict[str, Any]) -> MultiTimeframe:
    per_timeframe = raw.get("per_timeframe") if isinstance(raw.get("per_timeframe"), dict) else {}
    return MultiTimeframe(
        status=_availability_from_raw(raw),
        primary_timeframe=result.timeframe,
        alignment_score=_float_or_none(raw.get("alignment_score")),
        dominant_bias=_string_or_none(raw.get("dominant_bias")),
        per_timeframe_bias={
            str(timeframe): str(details.get("bias"))
            for timeframe, details in per_timeframe.items()
            if isinstance(details, dict) and details.get("bias")
        },
        conflict_notes=_list_of_strings(raw.get("conflict_notes")),
        entry_timing=_string_or_none(raw.get("entry_timing")),
        timeframes=per_timeframe,
        notes=_list_of_strings(raw.get("conflict_notes")) or _notes_from_raw(raw),
    )


def _regime_analysis(result: AnalysisResult, raw: dict[str, Any]) -> RegimeAnalysis:
    if _availability_from_raw(raw) == "not_available":
        return RegimeAnalysis(
            status="not_available",
            regime=result.market_regime.regime,
            volatility_state=result.market_regime.volatility_state,
            liquidity_condition=result.market_regime.liquidity_condition,
            notes=_notes_from_raw(raw) or list(result.market_regime.notes),
        )

    return RegimeAnalysis(
        status=_availability_from_raw(raw),
        regime=_string_or_none(raw.get("regime")) or result.market_regime.regime,
        regime_score=_float_or_none(raw.get("regime_score")),
        volatility_state=result.market_regime.volatility_state,
        liquidity_condition=result.market_regime.liquidity_condition,
        preferred_strategy=_string_or_none(raw.get("preferred_strategy")),
        risk_adjustment=_string_or_none(raw.get("risk_adjustment")),
        notes=_list_of_strings(raw.get("notes")) or list(result.market_regime.notes),
    )


def _market_structure(raw: dict[str, Any]) -> MarketStructure:
    return MarketStructure(
        status=_availability_from_raw(raw),
        structure=_string_or_none(raw.get("structure")),
        swing_pattern=raw.get("swing_pattern") if isinstance(raw.get("swing_pattern"), dict) else {},
        support=_float_or_none(raw.get("support")),
        resistance=_float_or_none(raw.get("resistance")),
        support_distance_pct=_float_or_none(raw.get("support_distance_pct")),
        resistance_distance_pct=_float_or_none(raw.get("resistance_distance_pct")),
        breakout_note=_string_or_none(raw.get("breakout_note")),
        rejection_note=_string_or_none(raw.get("rejection_note")),
        notes=_list_of_strings(raw.get("notes")),
    )


def _risk_plan(result: AnalysisResult) -> RiskPlan:
    risk = result.risk_summary
    return RiskPlan(
        status="available",
        risk_level=risk.risk_level,
        entry_area=risk.entry_area,
        stop_loss=risk.stop_loss,
        take_profit=risk.take_profit,
        risk_reward=risk.risk_reward,
        max_risk_pct=risk.max_risk_pct,
        notes=list(risk.notes),
    )


def _risk_gate(raw: dict[str, Any]) -> RiskGate:
    return RiskGate(
        status=_availability_from_raw(raw),
        risk_status=_string_or_none(raw.get("risk_status")),
        reasons=_list_of_strings(raw.get("reasons")) or _notes_from_raw(raw),
        raw=raw,
    )


def _data_quality(raw: dict[str, Any]) -> DataQuality:
    return DataQuality(
        status=_availability_from_raw(raw),
        score=_float_or_none(raw.get("score")),
        freshness_status=_freshness_status(raw),
        issues=_list_of_strings(raw.get("issues")) or _list_of_strings(raw.get("warnings")) or _notes_from_raw(raw),
        raw=raw,
    )


def _sentiment_context(result: AnalysisResult, sentiment_result: dict[str, Any] | None) -> SentimentContext:
    if not isinstance(sentiment_result, dict):
        sentiment_result = {}

    status = _availability_from_raw(sentiment_result)
    score = _float_or_none(sentiment_result.get("sentiment_score"))
    label = _string_or_none(sentiment_result.get("label")) or result.sentiment_summary.sentiment_label
    context = _list_of_strings(sentiment_result.get("context")) or list(result.sentiment_summary.context)
    notes = _list_of_strings(sentiment_result.get("key_topics"))
    notes.extend(_list_of_strings(sentiment_result.get("risk_keywords")))
    caveat = _string_or_none(sentiment_result.get("caveat"))
    reason = _string_or_none(sentiment_result.get("reason"))
    if caveat:
        notes.append(caveat)
    if reason:
        notes.append(reason)

    sentiment = result.sentiment_summary
    return SentimentContext(
        status=status,
        sentiment_label=label,
        sentiment_score=score if score is not None else sentiment.sentiment_score,
        context=context,
        source=_string_or_none(sentiment_result.get("source")) or sentiment.source,
        notes=notes,
    )


def _backtest_snapshot(backtest_result: dict[str, Any] | None, performance_summary: dict[str, Any] | None) -> BacktestSnapshot:
    backtest = backtest_result if isinstance(backtest_result, dict) else {}
    memory = performance_summary if isinstance(performance_summary, dict) else {}
    status = _availability_from_raw(backtest)
    metrics = {
        "backtest": backtest,
        "performance_memory": memory or _performance_memory_unavailable("Signal history memory was not evaluated."),
    }
    notes = _list_of_strings(backtest.get("notes"))
    caveat = backtest.get("caveat")
    if isinstance(caveat, str):
        notes.append(caveat)
    memory_caveat = memory.get("caveat") if isinstance(memory, dict) else None
    if isinstance(memory_caveat, str):
        notes.append(memory_caveat)

    return BacktestSnapshot(
        status=status,
        metrics=metrics,
        notes=notes or ["Backtest snapshot is not available."],
    )


def _validation_notes() -> ValidationNotes:
    return ValidationNotes(
        status="available",
        notes=[
            "Cockpit schema v1 is adapted from legacy AnalysisResult.",
            "Unavailable sections use status='not_available' instead of placeholder market data.",
        ],
    )


def _ui_sections() -> UiSections:
    order = [
        "price_snapshot",
        "market_overview",
        "market_context",
        "signal_decision",
        "confidence_breakdown",
        "evidence_layer",
        "multi_timeframe",
        "regime_analysis",
        "market_structure",
        "risk_plan",
        "risk_gate",
        "data_quality",
        "sentiment_context",
        "backtest_snapshot",
        "validation_notes",
    ]
    return UiSections(
        status="available",
        order=order,
        visible={section: True for section in order},
    )


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _performance_memory_unavailable(reason: str) -> dict[str, Any]:
    return {
        "status": "not_available",
        "sample_size": 0,
        "actionable_signals": 0,
        "blocked_or_invalid_signals": 0,
        "average_confidence": None,
        "caveat": "Performance memory is unavailable and must not be interpreted as proof of signal performance.",
        "notes": [reason],
    }


def _asset_class_for_symbol(symbol: str) -> str:
    normalized = symbol.upper()
    if normalized in {"BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD", "XRPUSD", "ADAUSD", "DOGEUSD", "AVAXUSD", "LINKUSD"}:
        return "crypto"
    if normalized in {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "GBPJPY"}:
        return "forex"
    if normalized in {"XAUUSD", "XAGUSD", "USOIL"}:
        return "commodity"
    return "equity"


def _price_source_label(source: object, provider_symbol: object) -> str:
    normalized = str(source or "unknown").lower()
    symbol = str(provider_symbol or "").strip()
    if normalized == "binance":
        return f"Binance Public Klines ({symbol})" if symbol else "Binance Public Klines"
    if normalized == "yahoo":
        return f"Yahoo Finance ({symbol})" if symbol else "Yahoo Finance"
    if normalized == "dummy":
        return "synthetic_fallback"
    return "market_data_service"


def _merge_sentiment_status(provider_status: object, scoring_status: object) -> str:
    provider = str(provider_status or "not_available").lower()
    scoring = str(scoring_status or "not_available").lower()
    if provider == "available" and scoring == "available":
        return "available"
    if provider in {"limited", "available"} and scoring in {"limited", "available"}:
        return "caution"
    if scoring == "limited":
        return "caution"
    return "not_available"


def _supported_timeframes(service: MarketDataService, primary_timeframe: str) -> list[str]:
    try:
        supported = list(service.get_supported_timeframes())
    except Exception:
        supported = ["M15", "M30", "H1", "H4", "D1"]
    normalized = [str(timeframe).upper() for timeframe in supported if timeframe]
    if primary_timeframe not in normalized:
        normalized.insert(0, primary_timeframe)
    return normalized


def _signal_validation(result: AnalysisResult, market_frame: pd.DataFrame | None) -> dict[str, Any]:
    latest = _latest_market_row(market_frame)
    close = _float_or_none(latest.get("Close")) if latest is not None else None
    technical = result.technical_summary
    distance_to_support = (close - technical.support) if close is not None else None
    distance_to_resistance = (technical.resistance - close) if close is not None else None
    atr_percent = (technical.atr / close * 100) if close else None

    return validate_signal_decision(
        signal=result.signal,
        bias=result.bias,
        trend=technical.trend,
        rsi=technical.rsi,
        atr_percent=atr_percent,
        distance_to_support=distance_to_support,
        distance_to_resistance=distance_to_resistance,
        risk_reward=result.risk_summary.risk_reward,
        risk_level=result.risk_level,
    )


def _availability_from_raw(raw: dict[str, Any]) -> str:
    status = str(raw.get("status", "")).lower()
    if not raw or status in {"unavailable", "not_available"}:
        return "not_available"
    if status in {"warning", "partial", "caution"}:
        return "caution"
    return "available"


def _notes_from_raw(raw: dict[str, Any]) -> list[str]:
    notes = _list_of_strings(raw.get("warnings"))
    notes.extend(note for note in _list_of_strings(raw.get("notes")) if note not in notes)
    reason = raw.get("reason")
    if isinstance(reason, str) and reason not in notes:
        notes.append(reason)
    if not raw and not notes:
        notes.append("Source data is not available from legacy AnalysisResult.")
    return notes


def _freshness_status(raw: dict[str, Any]) -> str | None:
    if "stale_data_detected" in raw:
        return "stale_or_unknown" if raw.get("stale_data_detected") is True else "fresh"
    if "data_is_fresh" not in raw:
        return None
    return "fresh" if raw.get("data_is_fresh") is True else "stale_or_unknown"


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _list_of_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _list_of_dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _latest_market_row(market_frame: pd.DataFrame | None) -> dict[str, Any] | None:
    if not isinstance(market_frame, pd.DataFrame) or market_frame.empty:
        return None
    try:
        return dict(market_frame.iloc[-1])
    except Exception:
        return None


def _float_or_none(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in {float("inf"), float("-inf")}:
        return None
    return number


def _timestamp_or_none(value: object) -> str | None:
    try:
        timestamp = pd.to_datetime(value, errors="coerce", utc=True)
    except Exception:
        return None
    if pd.isna(timestamp):
        return None
    return timestamp.isoformat()


_DEFAULT_COCKPIT_SERVICE = CockpitService()
