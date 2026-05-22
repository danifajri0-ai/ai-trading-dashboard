from __future__ import annotations

import pandas as pd
import streamlit as st

from apps.streamlit_app.ui.components import section_heading
from schemas import AnalysisResult


def render_market_table(
    result: AnalysisResult,
    market_frame: pd.DataFrame,
    radar_rows: list[dict[str, str]],
    show_radar: bool = True,
) -> None:
    section_heading(
        "Market Detail Information",
        "Audit teknikal, price action, struktur market, model sinyal, berita, dan integritas data.",
    )
    tabs = st.tabs(
        [
            "Technical Analysis",
            "Price Action",
            "ICT Strategy",
            "Market Structure",
            "Risk",
            "Signal Model",
            "News Context",
            "Data Integrity",
        ]
    )
    _render_technical_tab(tabs[0], result, market_frame)
    _render_price_action_tab(tabs[1], result, market_frame)
    _render_ict_tab(tabs[2], result, market_frame)
    _render_market_structure_tab(tabs[3], result)
    _render_risk_tab(tabs[4], result)
    _render_signal_model_tab(tabs[5], result)
    _render_news_tab(tabs[6], result)
    _render_integrity_tab(tabs[7], result)

    if show_radar:
        section_heading(
            "Market Radar",
            "Perbandingan multi-asset pada timeframe yang sama dengan chart aktif.",
        )
        if radar_rows:
            radar_frame = pd.DataFrame(radar_rows)
            st.dataframe(
                radar_frame.style.apply(_radar_row_style, axis=1),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "Market Radar memakai timeframe yang sama dengan chart aktif. "
                "Matikan dari sidebar jika ingin mode ringan."
            )
            _render_radar_heatmap(radar_frame)
        else:
            st.info("Belum ada data radar. Klik Analyze Market untuk memuat radar lintas pair.")


def _render_technical_tab(
    tab: st.delta_generator.DeltaGenerator,
    result: AnalysisResult,
    market_frame: pd.DataFrame,
) -> None:
    tech = result.technical_summary
    ema_spread = tech.ema_fast - tech.ema_slow
    spread_pct = (ema_spread / tech.ema_slow * 100) if tech.ema_slow else 0.0
    frame = pd.DataFrame(
        [
            ["EMA Fast", f"{tech.ema_fast:,.2f}", "EMA cepat"],
            ["EMA Slow", f"{tech.ema_slow:,.2f}", "EMA lambat"],
            ["EMA Spread", f"{ema_spread:,.2f}", f"Selisih EMA ({spread_pct:.2f}%)."],
            ["RSI", f"{tech.rsi:.2f}", _rsi_comment(tech.rsi)],
            ["ATR", f"{tech.atr:.2f}", f"Volatilitas: {result.market_regime.volatility_state}"],
            ["Support", f"{tech.support:,.2f}", "Area low terbaru"],
            ["Resistance", f"{tech.resistance:,.2f}", "Area high terbaru"],
        ],
        columns=["Metric", "Value", "Interpretation"],
    )
    with tab:
        st.dataframe(frame, use_container_width=True, hide_index=True)
        if not market_frame.empty:
            latest = market_frame.iloc[-1]
            st.caption(
                "Real market snapshot: "
                f"O {latest['Open']:.2f} | H {latest['High']:.2f} | "
                f"L {latest['Low']:.2f} | C {latest['Close']:.2f}"
            )


def _render_price_action_tab(
    tab: st.delta_generator.DeltaGenerator,
    result: AnalysisResult,
    market_frame: pd.DataFrame,
) -> None:
    with tab:
        ohlc_note = "-"
        candle_move = "-"
        volume_note = "-"
        if not market_frame.empty:
            last = market_frame.iloc[-1]
            prev = market_frame.iloc[-2] if len(market_frame) > 1 else last
            move_pct = ((last["Close"] - prev["Close"]) / max(prev["Close"], 1e-9)) * 100
            ohlc_note = f"O:{last['Open']:.2f} H:{last['High']:.2f} L:{last['Low']:.2f} C:{last['Close']:.2f}"
            candle_move = f"{move_pct:+.2f}%"
            if "Volume" in market_frame.columns:
                avg_vol = market_frame["Volume"].tail(40).mean()
                rel = last["Volume"] / max(avg_vol, 1.0)
                volume_note = f"{rel:.2f}x avg40"
        data = {
            "Item": ["Trend", "Bias", "Signal", "Reason", "OHLC Last Candle", "Candle Move", "Relative Volume"],
            "Value": [
                result.technical_summary.trend,
                result.bias,
                result.signal,
                result.reasons[0] if result.reasons else "-",
                ohlc_note,
                candle_move,
                volume_note,
            ],
        }
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


def _render_market_structure_tab(tab: st.delta_generator.DeltaGenerator, result: AnalysisResult) -> None:
    with tab:
        st.write(f"Regime: **{result.market_regime.regime}**")
        st.write(f"Liquidity: `{result.market_regime.liquidity_condition}`")
        for note in result.market_regime.notes:
            st.caption(note)


def _render_ict_tab(
    tab: st.delta_generator.DeltaGenerator,
    result: AnalysisResult,
    market_frame: pd.DataFrame,
) -> None:
    with tab:
        st.write("Checklist ringkas:")
        st.write("- Tunggu reaksi di area support/resistance.")
        st.write("- Hindari entry saat spread/volatilitas ekstrem.")
        st.write("- Konfirmasi candle sesuai bias sebelum eksekusi.")
        st.write("- Prioritaskan struktur market + rejection/continuation jelas.")
        if not market_frame.empty:
            st.write("- Gunakan volume spike sebagai konfirmasi tambahan untuk breakout.")
        if result.risk_summary.notes:
            st.caption(result.risk_summary.notes[0])


def _render_risk_tab(tab: st.delta_generator.DeltaGenerator, result: AnalysisResult) -> None:
    risk = result.risk_summary
    with tab:
        data = pd.DataFrame(
            [
                ["Risk Level", result.risk_level],
                ["Entry", _fmt(risk.entry_area)],
                ["Stop Loss", _fmt(risk.stop_loss)],
                ["Take Profit", _fmt(risk.take_profit)],
                ["Risk Reward", _fmt(risk.risk_reward)],
                ["Max Risk", f"{risk.max_risk_pct * 100:.1f}%"],
            ],
            columns=["Risk Metric", "Value"],
        )
        st.dataframe(data, use_container_width=True, hide_index=True)


def _render_signal_model_tab(tab: st.delta_generator.DeltaGenerator, result: AnalysisResult) -> None:
    with tab:
        rows = pd.DataFrame(
            [
                ["Signal", result.signal],
                ["Confidence", f"{result.confidence:.0f}%"],
                ["Trade Quality", f"{result.trade_quality_score:.0f}/100"],
                ["Summary", result.reasons[1] if len(result.reasons) > 1 else "-"],
            ],
            columns=["Component", "Output"],
        )
        st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_news_tab(tab: st.delta_generator.DeltaGenerator, result: AnalysisResult) -> None:
    with tab:
        sentiment = result.sentiment_summary
        st.write(f"Sentiment: **{sentiment.sentiment_label}** ({sentiment.sentiment_score:.1f})")
        context_rows = pd.DataFrame(
            [{"Context": line} for line in (sentiment.context or ["Belum ada konteks berita."])]
        )
        st.dataframe(context_rows, use_container_width=True, hide_index=True)
        st.caption(
            "News context ini bersifat ringkasan keputusan. "
            "Tahap selanjutnya bisa dihubungkan ke feed berita real-time."
        )


def _render_integrity_tab(tab: st.delta_generator.DeltaGenerator, result: AnalysisResult) -> None:
    with tab:
        st.write("Data policy:")
        st.write("- Analysis menggunakan data publik + provider service.")
        st.write("- Dashboard ini bersifat decision-support, bukan auto-execution.")
        st.write(f"- Source sentiment context: `{result.sentiment_summary.source}`")
        if result.warnings:
            st.caption("Warnings aktif menandakan kondisi market perlu kehati-hatian.")


def _render_context_cards(result: AnalysisResult) -> None:
    context_items = result.sentiment_summary.context[:4]
    while len(context_items) < 4:
        context_items.append("-")
    cards = [
        ("Konteks Aset", context_items[0]),
        ("Konteks Timeframe", context_items[1]),
        ("Checklist Sebelum Entry", context_items[2]),
        ("Data Policy", context_items[3]),
        ("Client Readiness", _client_readiness(result)),
    ]

    row1 = st.columns(2, gap="small")
    for col, (title, text) in zip(row1, cards[:2], strict=True):
        _context_card(col, title, text)

    row2 = st.columns(2, gap="small")
    for col, (title, text) in zip(row2, cards[2:4], strict=True):
        _context_card(col, title, text)

    row3 = st.columns(1)
    _context_card(row3[0], cards[4][0], cards[4][1])


def _render_radar_heatmap(frame: pd.DataFrame) -> None:
    section_heading("Mini Heatmap Market")
    heatmap = frame.copy()
    heatmap["Confidence"] = heatmap["Confidence"].str.replace("%", "", regex=False)
    heatmap["Confidence"] = pd.to_numeric(heatmap["Confidence"], errors="coerce").fillna(0.0)
    heatmap["Quality"] = pd.to_numeric(heatmap["Quality"], errors="coerce").fillna(0.0)
    risk_map = {"low": 80, "medium": 60, "high": 35, "extreme": 20}
    heatmap["RiskScore"] = heatmap["Risk"].map(risk_map).fillna(30)
    display = heatmap.set_index("Pair")[["Confidence", "Quality", "RiskScore"]]
    st.dataframe(
        display.style.background_gradient(cmap="RdYlGn", axis=None, vmin=0, vmax=100).format("{:.0f}"),
        use_container_width=True,
    )


def _context_card(col: st.delta_generator.DeltaGenerator, title: str, text: str) -> None:
    with col:
        st.markdown(
            f"""
            <div style="
                border:1px solid rgba(148,163,184,0.24);
                border-radius:12px;
                min-height:112px;
                padding:14px 14px;
                background:linear-gradient(135deg, rgba(9,23,43,0.7), rgba(15,23,42,0.84));">
                <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;">{title}</div>
                <div style="font-size:1.05rem;color:#e2e8f0;font-weight:600;line-height:1.35;">{text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _radar_row_style(row: pd.Series) -> list[str]:
    signal = str(row.get("Signal", ""))
    if signal.startswith("BUY"):
        return ["background-color: rgba(34,197,94,0.12)"] * len(row)
    if signal.startswith("SELL"):
        return ["background-color: rgba(239,68,68,0.12)"] * len(row)
    return ["background-color: rgba(245,158,11,0.08)"] * len(row)


def _fmt(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"


def _build_asset_comparison_rows(result: AnalysisResult) -> list[dict[str, str]]:
    tech = result.technical_summary
    risk = result.risk_summary
    return [
        {
            "Metric": "Signal Quality",
            "Current Asset": f"{result.trade_quality_score:.0f}/100",
            "Desk Baseline": ">= 60/100",
            "Status": "OK" if result.trade_quality_score >= 60 else "Review",
        },
        {
            "Metric": "Confidence",
            "Current Asset": f"{result.confidence:.0f}%",
            "Desk Baseline": ">= 55%",
            "Status": "OK" if result.confidence >= 55 else "Caution",
        },
        {
            "Metric": "Risk Level",
            "Current Asset": result.risk_level,
            "Desk Baseline": "LOW-MEDIUM",
            "Status": "OK" if result.risk_level in {"low", "medium"} else "High",
        },
        {
            "Metric": "RSI Position",
            "Current Asset": f"{tech.rsi:.2f}",
            "Desk Baseline": "40-60 (netral) / trend zone",
            "Status": "Watch",
        },
        {
            "Metric": "Risk Reward",
            "Current Asset": _fmt(risk.risk_reward),
            "Desk Baseline": ">= 1.50",
            "Status": "OK" if (risk.risk_reward or 0) >= 1.5 else "Low",
        },
    ]


def _rsi_comment(rsi: float) -> str:
    if rsi > 70:
        return "Overbought zone."
    if rsi < 30:
        return "Oversold zone."
    return "Netral."


def _client_readiness(result: AnalysisResult) -> str:
    return (
        "Sinyal dirangkum dari trend, momentum, area harga, volatilitas, "
        "dan risk plan sehingga mudah diaudit sebelum dipakai klien."
    )
