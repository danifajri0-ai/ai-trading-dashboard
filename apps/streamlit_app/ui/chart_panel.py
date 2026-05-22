from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from apps.streamlit_app.ui.components import section_heading
from schemas import AnalysisResult


def render_chart_panel(result: AnalysisResult, market_frame: pd.DataFrame) -> None:
    section_heading(
        f"Pro Chart: {_pair_label(result.symbol)}",
        "Konfirmasi visual dari candlestick, EMA, RSI, volume, support, dan resistance.",
    )
    st.caption("Chart menggunakan data market real-time snapshot dari provider aktif.")
    prepared = _prepare_chart_frame(market_frame)
    st.plotly_chart(_build_real_chart(result, prepared), use_container_width=True)

    section_heading(
        "AI Reasoning",
        "Penjelasan faktor teknikal yang membentuk alasan model saat ini.",
    )
    left, right = st.columns(2, gap="large")
    with left:
        _render_market_reading(result, prepared)
    with right:
        _render_signal_factors(result, prepared)


def _prepare_chart_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["Timestamp", "Open", "High", "Low", "Close", "Volume", "EMA20", "EMA50", "RSI14"]
    if frame is None or frame.empty:
        return pd.DataFrame(columns=columns)
    data = frame.copy()
    for column in ("Timestamp", "Open", "High", "Low", "Close", "Volume"):
        if column not in data.columns:
            return pd.DataFrame(columns=columns)
    data["Timestamp"] = pd.to_datetime(data["Timestamp"], errors="coerce", utc=True)
    for column in ("Open", "High", "Low", "Close", "Volume"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["Timestamp", "Open", "High", "Low", "Close"]).sort_values("Timestamp").reset_index(drop=True)
    if data.empty:
        return pd.DataFrame(columns=columns)

    close = data["Close"]
    data["EMA20"] = close.ewm(span=20, adjust=False).mean()
    data["EMA50"] = close.ewm(span=50, adjust=False).mean()
    data["RSI14"] = _compute_rsi(close, period=14)
    return data


def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def _build_real_chart(result: AnalysisResult, data: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.62, 0.24, 0.14],
    )
    if data.empty:
        fig.add_annotation(
            text="Data chart tidak tersedia",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(color="#cbd5e1", size=16),
        )
    else:
        fig.add_trace(
            go.Candlestick(
                x=data["Timestamp"],
                open=data["Open"],
                high=data["High"],
                low=data["Low"],
                close=data["Close"],
                increasing_line_color="#34d399",
                decreasing_line_color="#ef4444",
                name="Candlestick",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=data["Timestamp"], y=data["EMA20"], mode="lines", line=dict(color="#ff5a36", width=2), name="EMA 20"),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=data["Timestamp"], y=data["EMA50"], mode="lines", line=dict(color="#00e8c4", width=2), name="EMA 50"),
            row=1,
            col=1,
        )
        fig.add_hline(y=result.technical_summary.support, row=1, col=1, line_color="#22c55e", line_dash="dash")
        fig.add_hline(y=result.technical_summary.resistance, row=1, col=1, line_color="#ef4444", line_dash="dash")
        fig.add_trace(
            go.Scatter(x=data["Timestamp"], y=data["RSI14"], mode="lines", line=dict(color="#facc15", width=2), name="RSI 14"),
            row=2,
            col=1,
        )
        fig.add_hline(y=70, row=2, col=1, line_dash="dot", line_color="#ef4444")
        fig.add_hline(y=30, row=2, col=1, line_dash="dot", line_color="#22c55e")

        volume = data["Volume"].fillna(0.0)
        weighted_volume = volume / max(volume.max(), 1.0) * 100.0
        volume_colors = [
            "rgba(34,197,94,0.7)" if close >= open_ else "rgba(239,68,68,0.7)"
            for open_, close in zip(data["Open"], data["Close"], strict=True)
        ]
        fig.add_trace(
            go.Bar(x=data["Timestamp"], y=weighted_volume, marker_color=volume_colors, name="Volume"),
            row=3,
            col=1,
        )

    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=22, r=22, t=18, b=20),
        paper_bgcolor="rgba(2,6,23,0)",
        plot_bgcolor="rgba(2,6,23,0.55)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False,
        height=670,
    )
    fig.update_yaxes(title_text="Price", row=1, col=1, showgrid=True, gridcolor="rgba(148,163,184,0.16)")
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1, showgrid=True, gridcolor="rgba(148,163,184,0.16)")
    fig.update_yaxes(title_text="Vol", row=3, col=1, showgrid=True, gridcolor="rgba(148,163,184,0.16)")
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,0.12)")
    return fig


def _render_market_reading(result: AnalysisResult, data: pd.DataFrame) -> None:
    st.markdown("#### Market Reading")
    if data.empty:
        st.info("Data market belum tersedia untuk detail reading.")
        return

    last = data.iloc[-1]
    prev = data.iloc[-2] if len(data) > 1 else last
    candle_move_pct = ((last["Close"] - prev["Close"]) / max(prev["Close"], 1e-9)) * 100
    candle_range_pct = ((last["High"] - last["Low"]) / max(last["Close"], 1e-9)) * 100
    avg_volume = data["Volume"].tail(40).mean()
    rel_volume = last["Volume"] / max(avg_volume, 1.0)
    ema_spread = float(last["EMA20"] - last["EMA50"])
    span = max(result.technical_summary.resistance - result.technical_summary.support, 1e-6)
    position_in_range = (_close_proxy(result) - result.technical_summary.support) / span
    atr_pct = (result.technical_summary.atr / max(_close_proxy(result), 1e-6)) * 100
    momentum_grade = "Strong" if result.confidence >= 80 else "Medium" if result.confidence >= 60 else "Light"

    cards = [
        ("Trend Reading", result.technical_summary.trend),
        ("RSI Context", _rsi_context(result.technical_summary.rsi)),
        ("Volatility Interpretation", result.market_regime.volatility_state),
        ("Candle Move", _fmt_move(candle_move_pct)),
        ("Candle Range", f"{candle_range_pct:.2f}%"),
        ("Rel Volume", f"{rel_volume:.2f}x"),
        ("EMA Spread", f"{ema_spread:,.2f}"),
        ("ATR %", f"{atr_pct:.2f}%"),
        ("Range Position", f"{max(0, min(100, position_in_range * 100)):.1f}%"),
        ("Momentum Grade", momentum_grade),
    ]
    _render_info_cards(cards, 2)


def _render_signal_factors(result: AnalysisResult, data: pd.DataFrame) -> None:
    st.markdown("#### Signal Factors")
    summary = result.reasons[1] if len(result.reasons) > 1 else "Skenario model menunggu konfirmasi market."
    st.markdown(
        f"""
        <div class="fx-card" style="
            border:1px solid rgba(125,211,252,0.22);
            border-radius:12px;
            padding:14px 14px;
            background:linear-gradient(135deg, rgba(15,23,42,0.92), rgba(19,41,78,0.55));">
            <div style="display:flex;justify-content:space-between;align-items:baseline;">
                <div style="color:#94a3b8;text-transform:uppercase;font-size:12px;">Model Rationale</div>
                <div style="color:#38bdf8;font-size:1.1rem;font-weight:800;">Signal Factors</div>
            </div>
            <div style="color:#cbd5e1;font-size:1rem;line-height:1.45;">{summary}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    avg_volume = data["Volume"].tail(40).mean() if (not data.empty and "Volume" in data.columns) else 0.0
    rel_volume = (data["Volume"].iloc[-1] / max(avg_volume, 1.0)) if (not data.empty and "Volume" in data.columns) else 1.0
    volume_score = int(max(6, min(25, rel_volume * 8)))
    factors = [
        ("Trend", 30, "Trend mendukung skenario utama."),
        ("RSI", 20, _rsi_context(result.technical_summary.rsi)),
        ("Lokasi Harga", 14, _location_context(result)),
        ("Volatilitas", 15, f"Regime: {result.market_regime.volatility_state}."),
        ("Risk Plan", 15, _rr_context(result.risk_summary.risk_reward)),
        ("Sentiment", int(max(5, min(25, result.sentiment_summary.sentiment_score / 4))), _sentiment_context(result)),
        ("Liquidity", 12, result.market_regime.liquidity_condition),
        ("Volume", volume_score, _volume_context(data)),
    ]
    col1, col2 = st.columns(2, gap="small")
    for idx, (name, score, note) in enumerate(factors):
        with (col1 if idx % 2 == 0 else col2):
            _progress_factor(name, score, note)


def _progress_factor(name: str, score: int, note: str) -> None:
    normalized = max(0, min(100, int(score / 30 * 100)))
    st.markdown(
        f"""
        <div class="factor-group">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
                <div style="font-size:1.05rem;font-weight:700;color:#e2e8f0;">{name}</div>
                <div style="font-size:12px;color:#4ade80;background:rgba(15,23,42,0.8);padding:2px 8px;border-radius:999px;">{score} pts</div>
            </div>
            <div class="factor-track" style="margin-top:8px;">
                <div class="factor-fill" style="width:{normalized}%;"></div>
            </div>
            <div style="font-size:13px;color:#9ca3af;margin-top:8px;">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_info_cards(cards: list[tuple[str, str]], columns: int) -> None:
    for i in range(0, len(cards), columns):
        row = cards[i : i + columns]
        cols = st.columns(columns, gap="small")
        for j, (label, value) in enumerate(row):
            with cols[j]:
                st.markdown(
                    f"""
                    <div class="fx-card" style="
                        border:1px solid rgba(148,163,184,0.25);
                        border-radius:12px;
                        min-height:110px;
                        padding:12px 14px;
                        background:linear-gradient(135deg, rgba(7,27,41,0.66), rgba(15,23,42,0.82));">
                        <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;">{label}</div>
                        <div style="font-size:1.55rem;color:#e2e8f0;font-weight:700;line-height:1.15;">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _pair_label(symbol: str) -> str:
    if symbol.endswith("USD") and len(symbol) > 3:
        return f"{symbol[:-3]}/USD"
    return symbol


def _rsi_context(rsi: float) -> str:
    if rsi >= 70:
        return "RSI tinggi, risiko pullback meningkat."
    if rsi <= 30:
        return "RSI rendah, risiko rebound meningkat."
    return "RSI netral, menunggu dorongan arah."


def _location_context(result: AnalysisResult) -> str:
    tech = result.technical_summary
    midpoint = (tech.support + tech.resistance) / 2
    if _close_proxy(result) < midpoint:
        return "Harga dekat area support relatif."
    return "Harga cenderung di tengah sampai atas range."


def _rr_context(risk_reward: float | None) -> str:
    if risk_reward is None:
        return "Risk plan belum lengkap."
    if risk_reward >= 2:
        return "Risk-reward minimal 1:2 terpenuhi."
    if risk_reward >= 1.5:
        return "Risk-reward cukup, tetap selektif."
    return "Risk-reward belum ideal."


def _sentiment_context(result: AnalysisResult) -> str:
    return (
        f"{result.sentiment_summary.sentiment_label} "
        f"({result.sentiment_summary.sentiment_score:.1f}) - {result.sentiment_summary.source}"
    )


def _volume_context(data: pd.DataFrame) -> str:
    if data.empty or "Volume" not in data.columns:
        return "Volume belum tersedia."
    avg_volume = data["Volume"].tail(40).mean()
    rel_volume = data["Volume"].iloc[-1] / max(avg_volume, 1.0)
    return f"Relatif volume {rel_volume:.2f}x dari rata-rata 40 candle."


def _close_proxy(result: AnalysisResult) -> float:
    tech = result.technical_summary
    return (tech.ema_fast + tech.ema_slow) / 2


def _fmt_move(value: float) -> str:
    if value > 0:
        return f"UP +{value:.2f}%"
    if value < 0:
        return f"DOWN {value:.2f}%"
    return "FLAT 0.00%"
