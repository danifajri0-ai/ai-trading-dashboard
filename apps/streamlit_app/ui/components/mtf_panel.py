from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from apps.streamlit_app.ui.components._shared import badge, dataframe_from_mapping, metric, progress_bar, render_metrics, render_placeholder, status_tone, to_dict


def render_mtf_panel(result: Any) -> None:
    mtf = to_dict(to_dict(result).get("multi_timeframe"))
    if not mtf:
        render_placeholder("Multi-Timeframe", "not_available")
        return

    st.markdown(f"### Multi-Timeframe {badge(mtf.get('status'), status_tone(mtf.get('status')))}", unsafe_allow_html=True)
    render_metrics(
        [
            metric("Alignment", mtf.get("alignment_score"), tone=status_tone(mtf.get("status"))),
            metric("Dominant Bias", mtf.get("dominant_bias"), tone="info"),
            metric("Entry Timing", mtf.get("entry_timing"), tone="neutral"),
        ],
        columns=3,
    )
    st.markdown(progress_bar(mtf.get("alignment_score")), unsafe_allow_html=True)
    if mtf.get("timeframes"):
        st.dataframe(pd.DataFrame(dataframe_from_mapping(mtf["timeframes"])), use_container_width=True, hide_index=True)
    for note in mtf.get("conflict_notes", []) or []:
        st.warning(str(note))
