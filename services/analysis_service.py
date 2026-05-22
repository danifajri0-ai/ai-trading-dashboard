from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from domain.data_health_engine import evaluate_data_health
from domain.market_context_engine import build_market_context_lite
from domain.market_regime import (
    classify_market_regime,
    detect_liquidity_sweep,
    detect_simple_fvg,
    detect_volatility_regime,
    market_condition_warnings,
)
from domain.risk_gate_engine import evaluate_risk_gate
from domain.risk_engine import analyze_trend, calculate_risk_plan, classify_risk_level, risk_warnings, score_trade_quality
from domain.signal_contribution_engine import build_signal_contribution_lite
from domain.signal_explanation_engine import build_signal_explanation_lite
from domain.sentiment_engine import build_market_context, score_sentiment
from domain.signal_engine import build_signal_summary, empty_data_warnings, signal_warnings
from domain.technical_analysis import IndicatorSettings, add_indicators, calculate_levels
from schemas import AnalysisResult, MarketRegimeResult, RiskResult, SentimentSummary, TechnicalSummary
from services.market_data_service import MarketDataService


@dataclass(frozen=True)
class AnalysisService:
    market_data_service: MarketDataService
    indicator_settings: IndicatorSettings = IndicatorSettings()

    def analyze_market(self, symbol: str, timeframe: str) -> AnalysisResult:
        normalized_symbol = self.market_data_service.validate_symbol(symbol)
        normalized_timeframe = self.market_data_service.validate_timeframe(timeframe)
        data = self.market_data_service.get_market_data(normalized_symbol, normalized_timeframe)
        if data.empty:
            return _empty_result(normalized_symbol, normalized_timeframe)

        analyzed = add_indicators(data, self.indicator_settings)
        levels = calculate_levels(analyzed, self.indicator_settings)
        trend = analyze_trend(levels)
        risk_plan = calculate_risk_plan(levels, trend, self.indicator_settings)
        signal = build_signal_summary(levels, trend, risk_plan)

        pair_label = _to_pair_label(normalized_symbol)
        context_items = build_market_context(pair_label, _period_for_timeframe(normalized_timeframe), normalized_timeframe)
        sentiment = score_sentiment(pair_label, context_items)

        volatility_state = detect_volatility_regime(levels.atr_percent)
        sweep = detect_liquidity_sweep(analyzed)
        fvg = detect_simple_fvg(analyzed)
        regime = classify_market_regime(trend.direction, volatility_state)
        risk_level = classify_risk_level(levels.atr_percent)
        trade_quality_score = score_trade_quality(signal.confidence, risk_level)
        average_atr = _average_atr(analyzed)
        atr_ratio = (levels.atr / average_atr) if average_atr and average_atr > 0 else None
        rr_ratio = _resolve_rr_ratio(risk_plan.risk_reward, levels.distance_to_support, levels.distance_to_resistance, levels.atr)
        market_context_lite = build_market_context_lite(
            price=levels.latest_close,
            ema_20=levels.ema_fast,
            ema_50=levels.ema_slow,
            ema_200=_ema_200(analyzed),
            current_atr=levels.atr,
            average_atr=average_atr,
        )
        risk_gate_lite = evaluate_risk_gate(
            signal_score=signal.confidence,
            rr_ratio=rr_ratio,
            atr_ratio=atr_ratio,
            data_is_fresh=_is_data_fresh(levels.latest_time, normalized_timeframe),
            spread_is_safe=_spread_is_safe(analyzed, levels.latest_close),
        )
        data_health_lite = evaluate_data_health(
            candles=analyzed,
            expected_timeframe=normalized_timeframe,
            latest_timestamp=levels.latest_time,
        )
        signal_contribution_lite = build_signal_contribution_lite(
            trend_score=_trend_score(trend.direction),
            momentum_score=_momentum_score(levels.rsi, levels.macd_histogram),
            volume_score=_volume_score(analyzed),
            volatility_score=_volatility_score(levels.atr_percent),
            structure_score=_structure_score(levels.latest_close, levels.support, levels.resistance),
        )
        signal_explanation_lite = build_signal_explanation_lite(
            signal=signal.action,
            confidence=signal.confidence,
            market_context_lite=market_context_lite,
            risk_gate_lite=risk_gate_lite,
            data_health_lite=data_health_lite,
        )

        reasons = [
            trend.explanation,
            signal.summary,
            f"RSI: {levels.rsi:.2f}, ATR%: {levels.atr_percent:.2f}, MACD Hist: {levels.macd_histogram:.4f}",
        ]
        warnings = [
            *risk_warnings(risk_level),
            *signal_warnings(signal.action),
            *market_condition_warnings(sentiment.label),
        ]

        return AnalysisResult(
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            bias=_bias_from_direction(trend.direction),
            signal=signal.action,
            confidence=float(signal.confidence),
            risk_level=risk_level,
            trade_quality_score=float(trade_quality_score),
            reasons=reasons,
            warnings=warnings,
            technical_summary=TechnicalSummary(
                trend=trend.trend,
                ema_fast=levels.ema_fast,
                ema_slow=levels.ema_slow,
                rsi=levels.rsi,
                atr=levels.atr,
                support=levels.support,
                resistance=levels.resistance,
                notes=[f"MA: {levels.moving_average:.4f}", f"MACD: {levels.macd:.4f}"],
            ),
            sentiment_summary=SentimentSummary(
                sentiment_label=sentiment.label,
                sentiment_score=float(sentiment.score),
                context=[item.detail for item in context_items],
                source="rule_based_context",
            ),
            risk_summary=RiskResult(
                risk_level=risk_level,
                entry_area=risk_plan.entry_area,
                stop_loss=risk_plan.stop_loss,
                take_profit=risk_plan.take_profit,
                risk_reward=risk_plan.risk_reward,
                max_risk_pct=0.03,
                notes=[risk_plan.note],
            ),
            market_regime=MarketRegimeResult(
                regime=regime,
                volatility_state=volatility_state,
                liquidity_condition=sweep,
                notes=[fvg],
            ),
            market_context_lite=market_context_lite,
            risk_gate_lite=risk_gate_lite,
            data_health_lite=data_health_lite,
            signal_explanation_lite=signal_explanation_lite,
            signal_contribution_lite=signal_contribution_lite,
        )


_DEFAULT_ANALYSIS_SERVICE = AnalysisService(market_data_service=MarketDataService())


def analyze_market(symbol: str, timeframe: str) -> AnalysisResult:
    return _DEFAULT_ANALYSIS_SERVICE.analyze_market(symbol=symbol, timeframe=timeframe)


def _to_pair_label(symbol: str) -> str:
    mapping = {
        "XAUUSD": "XAU/USD",
        "BTCUSD": "BTC/USD",
        "ETHUSD": "ETH/USD",
        "SOLUSD": "SOL/USD",
        "EURUSD": "EUR/USD",
        "GBPUSD": "GBP/USD",
        "USDJPY": "USD/JPY",
        "AUDUSD": "AUD/USD",
        "USDCAD": "USD/CAD",
    }
    return mapping.get(symbol, symbol)


def _period_for_timeframe(timeframe: str) -> str:
    mapping = {"M15": "5d", "M30": "5d", "H1": "1mo", "H4": "3mo", "D1": "6mo"}
    return mapping.get(timeframe, "1mo")


def _bias_from_direction(direction: str) -> str:
    if direction == "BUY":
        return "BULLISH"
    if direction == "SELL":
        return "BEARISH"
    return "NEUTRAL"


def _ema_200(data: object) -> float | None:
    try:
        if data is None or data.empty or "Close" not in data.columns:
            return None
        return _safe_float(data["Close"].ewm(span=200, adjust=False).mean().iloc[-1])
    except Exception:
        return None


def _average_atr(data: object) -> float | None:
    try:
        if data is None or data.empty or "ATR" not in data.columns:
            return None
        return _safe_float(data["ATR"].tail(50).mean())
    except Exception:
        return None


def _safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in {float("inf"), float("-inf")}:
        return None
    return number


def _resolve_rr_ratio(
    risk_reward: object,
    distance_to_support: object,
    distance_to_resistance: object,
    atr: object,
) -> float | None:
    direct = _safe_float(risk_reward)
    if direct is not None and direct > 0:
        return direct

    atr_value = _safe_float(atr)
    support_distance = _safe_float(distance_to_support)
    resistance_distance = _safe_float(distance_to_resistance)
    if atr_value is None or atr_value <= 0 or support_distance is None or resistance_distance is None:
        return None

    # Use the smaller side distance as a conservative fallback proxy.
    closest_distance = min(abs(support_distance), abs(resistance_distance))
    if closest_distance <= 0:
        return None
    return closest_distance / atr_value


def _is_data_fresh(latest_time: object, timeframe: str) -> bool:
    try:
        timestamp = pd.to_datetime(latest_time, errors="coerce", utc=True)
    except Exception:
        return False
    if pd.isna(timestamp):
        return False

    age = pd.Timestamp.now(tz="UTC") - timestamp
    future_tolerance = pd.Timedelta(minutes=5)
    if age < -future_tolerance:
        return False
    return age <= _freshness_limit(timeframe)


def _freshness_limit(timeframe: str) -> pd.Timedelta:
    mapping = {
        "M15": pd.Timedelta(minutes=45),
        "M30": pd.Timedelta(minutes=90),
        "H1": pd.Timedelta(hours=3),
        "H4": pd.Timedelta(hours=12),
        "D1": pd.Timedelta(days=3),
    }
    return mapping.get(timeframe.upper(), pd.Timedelta(hours=3))


def _spread_is_safe(data: object, latest_close: object) -> bool:
    try:
        if data is None or data.empty:
            return True
        bid_column = _first_existing_column(data, ("Bid", "bid", "BestBid", "best_bid"))
        ask_column = _first_existing_column(data, ("Ask", "ask", "BestAsk", "best_ask"))
        if bid_column is None or ask_column is None:
            return True

        bid = _safe_float(data[bid_column].iloc[-1])
        ask = _safe_float(data[ask_column].iloc[-1])
        close = _safe_float(latest_close)
        if bid is None or ask is None or close is None or close <= 0 or ask < bid:
            return False
        spread_pct = (ask - bid) / close
        return spread_pct <= 0.005
    except Exception:
        return True


def _first_existing_column(data: object, candidates: tuple[str, ...]) -> str | None:
    for column in candidates:
        if column in data.columns:
            return column
    return None


def _unavailable_lite_result() -> dict[str, object]:
    return {
        "status": "unavailable",
        "reason": "required inputs missing",
    }


def _empty_result(symbol: str, timeframe: str) -> AnalysisResult:
    return AnalysisResult(
        symbol=symbol,
        timeframe=timeframe,
        bias="NEUTRAL",
        signal="WAIT",
        confidence=0.0,
        risk_level="high",
        trade_quality_score=0.0,
        reasons=["Data market kosong sehingga analisa tidak dapat dihitung."],
        warnings=empty_data_warnings(),
        technical_summary=TechnicalSummary(
            trend="No Data",
            ema_fast=0.0,
            ema_slow=0.0,
            rsi=50.0,
            atr=0.0,
            support=0.0,
            resistance=0.0,
            notes=["Indikator tidak tersedia karena data kosong."],
        ),
        sentiment_summary=SentimentSummary(
            sentiment_label="Neutral",
            sentiment_score=50.0,
            context=["Belum ada data untuk membangun konteks market."],
            source="empty_data_fallback",
        ),
        risk_summary=RiskResult(
            risk_level="high",
            entry_area=None,
            stop_loss=None,
            take_profit=None,
            risk_reward=None,
            max_risk_pct=0.03,
            notes=["Hindari entry sampai data valid tersedia."],
        ),
        market_regime=MarketRegimeResult(
            regime="UNKNOWN",
            volatility_state="Unknown",
            liquidity_condition="Insufficient candles",
            notes=["Regime market belum dapat ditentukan."],
        ),
        market_context_lite=_unavailable_lite_result(),
        risk_gate_lite=_unavailable_lite_result(),
        data_health_lite=_unavailable_lite_result(),
        signal_explanation_lite=_unavailable_lite_result(),
        signal_contribution_lite=_unavailable_lite_result(),
    )


def _trend_score(direction: object) -> float | None:
    if direction == "BUY":
        return 72.0
    if direction == "SELL":
        return 72.0
    if direction == "WAIT":
        return 45.0
    return None


def _momentum_score(rsi: object, macd_histogram: object) -> float | None:
    rsi_value = _safe_float(rsi)
    macd_hist = _safe_float(macd_histogram)
    if rsi_value is None or macd_hist is None:
        return None
    rsi_component = max(0.0, min(100.0, 100.0 - abs(rsi_value - 50.0) * 2.0))
    macd_component = max(0.0, min(100.0, 50.0 + (macd_hist * 500.0)))
    return max(0.0, min(100.0, (rsi_component * 0.6) + (macd_component * 0.4)))


def _volume_score(data: object) -> float | None:
    try:
        if data is None or data.empty or "Volume" not in data.columns:
            return None
        series = pd.to_numeric(data["Volume"], errors="coerce").dropna()
        if series.empty:
            return None
        recent = _safe_float(series.iloc[-1])
        avg_40 = _safe_float(series.tail(40).mean())
        if recent is None or avg_40 is None or avg_40 <= 0:
            return None
        ratio = recent / avg_40
        return max(0.0, min(100.0, ratio * 50.0))
    except Exception:
        return None


def _volatility_score(atr_percent: object) -> float | None:
    atr_pct = _safe_float(atr_percent)
    if atr_pct is None:
        return None
    distance = abs(atr_pct - 1.5)
    return max(0.0, min(100.0, 100.0 - (distance * 40.0)))


def _structure_score(latest_close: object, support: object, resistance: object) -> float | None:
    close = _safe_float(latest_close)
    sup = _safe_float(support)
    res = _safe_float(resistance)
    if close is None or sup is None or res is None or res <= sup:
        return None
    range_size = res - sup
    if range_size <= 0:
        return None
    position = (close - sup) / range_size
    centered = abs(position - 0.5) * 2.0
    return max(0.0, min(100.0, 100.0 - (centered * 100.0)))
