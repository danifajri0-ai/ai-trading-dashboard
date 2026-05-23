from __future__ import annotations

from typing import Any

import streamlit as st

from apps.streamlit_app.ui.components._shared import badge, metric, render_list, render_metrics, render_placeholder, status_tone, to_dict


def render_backtest_panel(result: Any) -> None:
    snapshot = to_dict(to_dict(result).get("backtest_snapshot"))
    if not snapshot:
        render_placeholder("Backtest Snapshot", "not_available")
        return

    metrics = to_dict(snapshot.get("metrics"))
    backtest = to_dict(metrics.get("backtest"))
    memory = to_dict(metrics.get("performance_memory"))
    st.markdown(f"### Backtest Snapshot {badge(snapshot.get('status'), status_tone(snapshot.get('status')))}", unsafe_allow_html=True)
    render_metrics(
        [
            metric("Sample", backtest.get("sample_size"), tone="info"),
            metric("Est. Win Rate", backtest.get("estimated_win_rate"), tone="warn"),
            metric("Avg R:R", backtest.get("avg_rr"), tone="info"),
            metric("DD Estimate", backtest.get("max_drawdown_estimate"), tone="warn"),
            metric("Memory", memory.get("sample_size"), tone=status_tone(memory.get("status"))),
        ],
        columns=3,
    )
    with st.expander("Caveats", expanded=True):
        st.markdown(render_list(snapshot.get("notes", []), "Backtest belum tersedia."), unsafe_allow_html=True)
