from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from schemas import AnalysisResult, MarketRegimeResult, RiskResult, SentimentSummary, TechnicalSummary


DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"


class ApiClientError(RuntimeError):
    """Raised when HTTP API call fails or returns invalid payload."""


def get_health(base_url: str = DEFAULT_API_BASE_URL) -> dict[str, str]:
    return _get_json(f"{base_url}/health")


def get_symbols(base_url: str = DEFAULT_API_BASE_URL) -> dict[str, list[str]]:
    payload = _get_json(f"{base_url}/symbols")
    symbols = payload.get("symbols", [])
    timeframes = payload.get("timeframes", [])
    if not isinstance(symbols, list) or not isinstance(timeframes, list):
        raise ApiClientError("Invalid symbols payload from backend.")
    return {"symbols": [str(item) for item in symbols], "timeframes": [str(item) for item in timeframes]}


def analyze_market_http(symbol: str, timeframe: str, base_url: str = DEFAULT_API_BASE_URL) -> AnalysisResult:
    payload = _post_json(
        f"{base_url}/analyze",
        {"symbol": symbol, "timeframe": timeframe},
    )
    return _analysis_result_from_dict(payload)


def _analysis_result_from_dict(payload: dict) -> AnalysisResult:
    try:
        technical = payload["technical_summary"]
        sentiment = payload["sentiment_summary"]
        risk = payload["risk_summary"]
        regime = payload["market_regime"]
        return AnalysisResult(
            symbol=str(payload["symbol"]),
            timeframe=str(payload["timeframe"]),
            bias=str(payload["bias"]),
            signal=str(payload["signal"]),
            confidence=float(payload["confidence"]),
            risk_level=str(payload["risk_level"]),
            trade_quality_score=float(payload["trade_quality_score"]),
            reasons=[str(item) for item in payload.get("reasons", [])],
            warnings=[str(item) for item in payload.get("warnings", [])],
            technical_summary=TechnicalSummary(
                trend=str(technical["trend"]),
                ema_fast=float(technical["ema_fast"]),
                ema_slow=float(technical["ema_slow"]),
                rsi=float(technical["rsi"]),
                atr=float(technical["atr"]),
                support=float(technical["support"]),
                resistance=float(technical["resistance"]),
                notes=[str(item) for item in technical.get("notes", [])],
            ),
            sentiment_summary=SentimentSummary(
                sentiment_label=str(sentiment["sentiment_label"]),
                sentiment_score=float(sentiment["sentiment_score"]),
                context=[str(item) for item in sentiment.get("context", [])],
                source=str(sentiment.get("source", "http_api")),
            ),
            risk_summary=RiskResult(
                risk_level=str(risk["risk_level"]),
                entry_area=_float_or_none(risk.get("entry_area")),
                stop_loss=_float_or_none(risk.get("stop_loss")),
                take_profit=_float_or_none(risk.get("take_profit")),
                risk_reward=_float_or_none(risk.get("risk_reward")),
                max_risk_pct=float(risk["max_risk_pct"]),
                notes=[str(item) for item in risk.get("notes", [])],
            ),
            market_regime=MarketRegimeResult(
                regime=str(regime["regime"]),
                volatility_state=str(regime["volatility_state"]),
                liquidity_condition=str(regime["liquidity_condition"]),
                notes=[str(item) for item in regime.get("notes", [])],
            ),
            market_context_lite=_dict_or_none(payload.get("market_context_lite")),
            risk_gate_lite=_dict_or_none(payload.get("risk_gate_lite")),
            data_health_lite=_dict_or_none(payload.get("data_health_lite")),
            signal_explanation_lite=_dict_or_none(payload.get("signal_explanation_lite")),
            signal_contribution_lite=_dict_or_none(payload.get("signal_contribution_lite")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ApiClientError(f"Invalid analysis payload from backend: {exc}") from exc


def _get_json(url: str) -> dict:
    try:
        with urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError) as exc:
        raise ApiClientError(f"GET request failed: {exc}") from exc


def _post_json(url: str, payload: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError) as exc:
        raise ApiClientError(f"POST request failed: {exc}") from exc


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _dict_or_none(value: object) -> dict | None:
    if isinstance(value, dict):
        return value
    return None
