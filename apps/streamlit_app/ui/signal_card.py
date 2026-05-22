from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

from apps.streamlit_app.ui.components import metric_card, render_grid, section_heading, status_pill
from schemas import AnalysisResult


def render_signal_card(result: AnalysisResult, market_frame: pd.DataFrame) -> None:
    pair = _pair_label(result.symbol)
    profile = _market_profile(result, market_frame)
    has_lite_context = _available_dict(getattr(result, "market_context_lite", None)) is not None

    status_items = [
        status_pill("Pair", pair, "info"),
        status_pill("Timeframe", result.timeframe, "neutral"),
        status_pill("Data Status", profile["data_status"], _quality_tone(profile["data_quality"])),
        status_pill("Last Candle", profile["last_candle"], "neutral"),
        status_pill("Data Age", profile["data_age"], _quality_tone(profile["data_quality"])),
        status_pill("Source", "Public market feed", "info"),
    ]
    general_cards = []
    if not has_lite_context:
        general_cards.extend(
            [
                metric_card("Market Regime", result.market_regime.regime.title(), "Struktur market aktif", "info", compact=True),
                metric_card("Volatility Regime", result.market_regime.volatility_state, "Kondisi ATR saat ini", "warn", compact=True),
            ]
        )
    general_cards.extend(
        [
        metric_card("Session Context", profile["session_context"], "Jam market dominan", "neutral", compact=True),
        metric_card("Data Quality", profile["data_quality"], "Kelayakan data untuk analisa", _quality_tone(profile["data_quality"]), compact=True),
        metric_card("Range Position", profile["range_position"], "Posisi harga dalam support-resistance", "info", compact=True),
        metric_card("Relative Volume", profile["relative_volume"], "Volume vs rata-rata 40 candle", "good", compact=True),
        ]
    )

    st.markdown(
        f"""
        <section class="hero-panel fx-card">
          <div class="hero-copy">
            <div class="hero-kicker">AI Trading Terminal</div>
            <h1>AI Trading Dashboard</h1>
            <h2>{pair} Trading Desk</h2>
            <p>
              Pantau arah market, momentum, area harga penting, dan rencana risiko
              dalam satu tampilan profesional.
            </p>
          </div>
          <div class="status-bar">{''.join(status_items)}</div>
          <div class="hero-subsection">
            <div class="subsection-title">General Market Information</div>
            {render_grid(general_cards, columns=6)}
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    section_heading(
        "Market Overview",
        "Ringkasan kondisi market untuk validasi cepat sebelum membaca keputusan sinyal.",
    )
    overview_cards = [
        metric_card("Price", f"{profile['price']:,.2f}", "Harga close terakhir", "info"),
        metric_card("Market Status", profile["data_status"], "Status data market aktif", _quality_tone(profile["data_quality"])),
        metric_card("Last Candle", profile["last_candle"], "Timestamp candle terbaru", "neutral"),
        metric_card("Data Age", profile["data_age"], "Umur data terhadap waktu sekarang", _quality_tone(profile["data_quality"])),
        metric_card("Range Position", profile["range_position"], "Posisi harga dalam support-resistance", "info"),
        metric_card("Relative Volume", profile["relative_volume"], "Volume vs rata-rata 40 candle", "good"),
        metric_card("RSI", f"{result.technical_summary.rsi:.2f}", "Momentum 14 periode", "info"),
        metric_card("ATR", f"{result.technical_summary.atr:.2f}", "Volatilitas absolut", "good"),
    ]
    st.markdown(render_grid(overview_cards, columns=4), unsafe_allow_html=True)
    _render_market_regime_lite(result)

    section_heading(
        "Signal Decision",
        "Keputusan model yang siap dipakai sebagai acuan eksekusi.",
    )
    _render_signal_decision(result)


def _render_signal_decision(result: AnalysisResult) -> None:
    decision_cards = [
        metric_card("Signal", result.signal, "Keputusan model saat ini", _signal_tone(result.signal)),
        metric_card("Confidence", f"{result.confidence:.0f}%", "Keyakinan model", "info"),
        metric_card("Bias", result.bias, "Arah dominan market", _bias_tone(result.bias)),
        metric_card("Quality", f"{result.trade_quality_score:.0f}/100", "Kualitas setup", "warn"),
        metric_card("Risk", result.risk_level.upper(), "Level risiko setup", _risk_tone(result.risk_level)),
    ]
    risk = result.risk_summary
    note = risk.notes[0] if risk.notes else "Gunakan risk plan sebagai kontrol eksekusi."
    title = _setup_title(result.signal)
    st.markdown(
        f"""
        <section class="setup-panel fx-card">
          <div>
            <div class="metric-label">{_pair_label(result.symbol)} Decision Card</div>
            <div class="setup-title tone-text-{_signal_tone(result.signal)}">{title}</div>
            <p>{note}</p>
          </div>
          {render_grid(decision_cards, columns=5)}
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_market_regime_lite(result: AnalysisResult) -> None:
    context = _available_dict(getattr(result, "market_context_lite", None))
    if not context:
        return

    section_heading("Market Context")
    cards = [
        metric_card("Regime", _label(context.get("regime_label")), "Context lite", "info", compact=True),
        metric_card("Volatility", _label(context.get("volatility_state")), "ATR regime", _volatility_tone(context.get("volatility_state")), compact=True),
        metric_card("Trend", _label(context.get("trend_state")), "MA alignment", _trend_state_tone(context.get("trend_state")), compact=True),
    ]
    st.markdown(render_grid(cards, columns=3), unsafe_allow_html=True)


def _market_profile(result: AnalysisResult, frame: pd.DataFrame) -> dict[str, str | float]:
    data_status = _data_status(result)
    last_candle = "-"
    data_age = "-"
    price = _close_proxy(result)
    relative_volume = "-"
    range_position = _range_position(result, price)

    if frame is not None and not frame.empty and "Timestamp" in frame.columns:
        data = frame.copy()
        data["Timestamp"] = pd.to_datetime(data["Timestamp"], errors="coerce", utc=True)
        data = data.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)
        if not data.empty:
            latest = data.iloc[-1]
            timestamp = latest["Timestamp"]
            last_candle = timestamp.strftime("%Y-%m-%d %H:%M")
            data_age = _human_age(timestamp)
            if "Close" in data.columns and pd.notna(latest.get("Close")):
                price = float(latest["Close"])
                range_position = _range_position(result, price)
            if "Volume" in data.columns:
                avg_volume = pd.to_numeric(data["Volume"], errors="coerce").tail(40).mean()
                latest_volume = pd.to_numeric(pd.Series([latest.get("Volume")]), errors="coerce").iloc[0]
                if pd.notna(avg_volume) and avg_volume > 0 and pd.notna(latest_volume):
                    relative_volume = f"{latest_volume / avg_volume:.2f}x"

    data_quality = _data_quality(data_status, data_age)
    return {
        "data_status": data_status,
        "last_candle": last_candle,
        "data_age": data_age,
        "price": price,
        "session_context": _session_context(),
        "range_position": range_position,
        "relative_volume": relative_volume,
        "data_quality": data_quality,
    }


def _pair_label(symbol: str) -> str:
    if symbol.endswith("USD") and len(symbol) > 3:
        return f"{symbol[:-3]}/USD"
    return symbol


def _close_proxy(result: AnalysisResult) -> float:
    tech = result.technical_summary
    return (tech.ema_fast + tech.ema_slow) / 2


def _range_position(result: AnalysisResult, price: float) -> str:
    support = result.technical_summary.support
    resistance = result.technical_summary.resistance
    span = max(resistance - support, 1e-6)
    position = max(0.0, min(100.0, ((price - support) / span) * 100))
    return f"{position:.1f}%"


def _human_age(timestamp: pd.Timestamp) -> str:
    now = pd.Timestamp(datetime.now(timezone.utc))
    minutes = max(0, int((now - timestamp).total_seconds() // 60))
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 48:
        return f"{hours}h"
    return f"{hours // 24}d"


def _session_context() -> str:
    hour = datetime.now(timezone.utc).hour
    if 0 <= hour < 7:
        return "Asia"
    if 7 <= hour < 13:
        return "London"
    if 13 <= hour < 16:
        return "Overlap"
    if 16 <= hour < 21:
        return "New York"
    return "Late US"


def _data_status(result: AnalysisResult) -> str:
    return "Unavailable" if any("Data kosong" in warning for warning in result.warnings) else "Fresh"


def _data_quality(data_status: str, data_age: str) -> str:
    if data_status == "Unavailable":
        return "Weak"
    if data_age.endswith("d"):
        return "Delayed"
    return "Fresh"


def _quality_tone(value: str) -> str:
    if value in {"Fresh", "Normal"}:
        return "good"
    if value == "Delayed":
        return "warn"
    if value in {"Weak", "Unavailable"}:
        return "bad"
    return "neutral"


def _setup_title(signal: str) -> str:
    if signal.startswith("BUY"):
        return "BUY Setup"
    if signal.startswith("SELL"):
        return "SELL Setup"
    return "WAIT Setup"


def _signal_tone(signal: str) -> str:
    if signal.startswith("BUY"):
        return "good"
    if signal.startswith("SELL"):
        return "bad"
    return "warn"


def _bias_tone(bias: str) -> str:
    if bias == "BULLISH":
        return "good"
    if bias == "BEARISH":
        return "bad"
    return "warn"


def _risk_tone(level: str) -> str:
    if level == "low":
        return "good"
    if level == "medium":
        return "warn"
    return "bad"


def _available_dict(value: object) -> dict[str, Any] | None:
    if isinstance(value, dict) and value.get("status") != "unavailable":
        return value
    return None


def _label(value: object) -> str:
    if value is None:
        return "-"
    text = str(value).replace("_", " ").strip()
    return text.title() if text else "-"


def _volatility_tone(value: object) -> str:
    if value == "high_volatility":
        return "bad"
    if value == "low_volatility":
        return "warn"
    if value == "normal_volatility":
        return "good"
    return "neutral"


def _trend_state_tone(value: object) -> str:
    if value == "bullish_trend":
        return "good"
    if value == "bearish_trend":
        return "bad"
    if value == "mixed_or_range":
        return "warn"
    return "neutral"
