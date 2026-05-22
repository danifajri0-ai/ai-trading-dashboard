from __future__ import annotations

import streamlit as st

from schemas import AnalysisResult


def render_header() -> None:
    st.title("AI Trading Dashboard")
    st.caption("Service-driven market analysis")


def render_result(result: AnalysisResult) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Signal", result.signal)
    col2.metric("Confidence", f"{result.confidence:.0f}%")
    col3.metric("Risk", result.risk_level)
    col4.metric("Quality", f"{result.trade_quality_score:.0f}/100")

    st.subheader("Overview")
    st.write(f"Symbol: `{result.symbol}`")
    st.write(f"Timeframe: `{result.timeframe}`")
    st.write(f"Bias: `{result.bias}`")

    st.subheader("Technical Summary")
    tech = result.technical_summary
    st.write(f"Trend: {tech.trend}")
    st.write(f"EMA Fast / Slow: {tech.ema_fast:,.4f} / {tech.ema_slow:,.4f}")
    st.write(f"RSI: {tech.rsi:.2f}")
    st.write(f"ATR: {tech.atr:.4f}")
    st.write(f"Support / Resistance: {tech.support:,.4f} / {tech.resistance:,.4f}")
    for note in tech.notes:
        st.caption(note)

    st.subheader("Risk Summary")
    risk = result.risk_summary
    st.write(f"Entry: {_fmt(risk.entry_area)}")
    st.write(f"Stop Loss: {_fmt(risk.stop_loss)}")
    st.write(f"Take Profit: {_fmt(risk.take_profit)}")
    st.write(f"Risk Reward: {_fmt(risk.risk_reward)}")
    for note in risk.notes:
        st.caption(note)

    st.subheader("Sentiment & Regime")
    sentiment = result.sentiment_summary
    regime = result.market_regime
    st.write(f"Sentiment: {sentiment.sentiment_label} ({sentiment.sentiment_score:.1f})")
    st.write(f"Regime: {regime.regime} | Volatility: {regime.volatility_state}")
    st.write(f"Liquidity: {regime.liquidity_condition}")
    for note in regime.notes:
        st.caption(note)

    st.subheader("Reasons")
    for reason in result.reasons:
        st.write(f"- {reason}")

    st.subheader("Warnings")
    if result.warnings:
        for warning in result.warnings:
            st.warning(warning)
    else:
        st.success("Tidak ada warning kritis pada setup saat ini.")


def _fmt(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.4f}"

