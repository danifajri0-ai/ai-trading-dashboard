from __future__ import annotations

from typing import Any

import streamlit as st

from apps.streamlit_app.ui.components._shared import badge, metric, progress_bar, render_list, render_metrics, render_placeholder, status_tone, to_dict


def render_data_quality_panel(result: Any) -> None:
    quality = to_dict(to_dict(result).get("data_quality"))
    if not quality:
        render_placeholder("Data Quality", "not_available")
        return

    raw = to_dict(quality.get("raw"))
    st.markdown(f"### Data Quality {badge(quality.get('status'), status_tone(quality.get('status')))}", unsafe_allow_html=True)
    render_metrics(
        [
            metric("Score", quality.get("score"), tone=status_tone(quality.get("status"))),
            metric("Freshness", quality.get("freshness_status"), tone=status_tone(quality.get("freshness_status"))),
            metric("Candles", raw.get("candle_count"), tone="info"),
        ],
        columns=3,
    )
    st.markdown(progress_bar(quality.get("score")), unsafe_allow_html=True)
    st.markdown(render_list(quality.get("issues", []), "Tidak ada issue data quality."), unsafe_allow_html=True)
