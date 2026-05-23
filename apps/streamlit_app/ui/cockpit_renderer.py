from __future__ import annotations

from typing import Any

import streamlit as st

from apps.streamlit_app.ui.components.backtest_panel import render_backtest_panel
from apps.streamlit_app.ui.components.chart_zone_panel import render_post_chart_summary, render_pro_chart
from apps.streamlit_app.ui.components.data_quality_panel import render_data_quality_panel
from apps.streamlit_app.ui.components.decision_lab_panel import render_decision_lab_panel
from apps.streamlit_app.ui.components.evidence_panel import render_evidence_layer
from apps.streamlit_app.ui.components.heatmap_panel import render_signal_heatmap
from apps.streamlit_app.ui.components.market_overview_panel import render_market_state_strip
from apps.streamlit_app.ui.components.market_radar_panel import render_market_radar_panel
from apps.streamlit_app.ui.components.mtf_panel import render_mtf_panel
from apps.streamlit_app.ui.components.regime_panel import render_regime_panel
from apps.streamlit_app.ui.components.risk_panel import render_risk_execution_console
from apps.streamlit_app.ui.components.sentiment_panel import render_sentiment_panel
from apps.streamlit_app.ui.components.signal_decision_panel import render_signal_command_center
from apps.streamlit_app.ui.components.trading_desk_header import render_command_header
from apps.streamlit_app.ui.components._shared import section_title
from apps.streamlit_app.ui.styles.cockpit_css import render_cockpit_css


def render_cockpit(result: Any, source: str = "local") -> None:
    render_cockpit_css()
    render_command_header(result, source=source)
    render_pro_chart(result)
    render_post_chart_summary(result)

    top_left, top_right = st.columns([1.1, 0.9], gap="large")
    with top_left:
        render_market_state_strip(result)
        render_signal_command_center(result)
    with top_right:
        render_risk_execution_console(result)

    section_title(
        "Deep Analysis Console",
        eyebrow="Evidence Workspace",
        meta="Evidence, heatmap, regime, data, and validation context",
    )
    tabs = st.tabs(["Evidence", "Timeframes", "Regime", "Data", "Performance", "Sentiment", "Radar"])
    with tabs[0]:
        render_evidence_layer(result)
        render_signal_heatmap(result)
    with tabs[1]:
        render_mtf_panel(result)
    with tabs[2]:
        render_regime_panel(result)
    with tabs[3]:
        render_data_quality_panel(result)
    with tabs[4]:
        render_backtest_panel(result)
    with tabs[5]:
        render_sentiment_panel(result)
    with tabs[6]:
        left, right = st.columns(2, gap="large")
        with left:
            render_market_radar_panel(result)
        with right:
            render_decision_lab_panel(result)
