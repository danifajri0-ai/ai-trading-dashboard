from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from apps.streamlit_app.ui.components._shared import badge, render_placeholder, status_tone, to_dict


def render_market_radar_panel(result: Any) -> None:
    mtf = to_dict(to_dict(result).get("multi_timeframe"))
    if not mtf:
        render_placeholder("Market Radar", "not_available", "Radar needs multi-timeframe data from the current analysis.")
        return

    rows = []
    for timeframe, bias in mtf.get("per_timeframe_bias", {}).items():
        rows.append({"Timeframe": timeframe, "Bias": bias, "Dominant": mtf.get("dominant_bias"), "Entry Timing": mtf.get("entry_timing")})
    st.markdown(f"### Market Radar {badge(mtf.get('status'), status_tone(mtf.get('status')))}", unsafe_allow_html=True)
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Market radar is currently unavailable for this analysis.")
