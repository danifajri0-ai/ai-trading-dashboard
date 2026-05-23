from __future__ import annotations

from typing import Any

import streamlit as st

from apps.streamlit_app.ui.components._shared import badge, metric, progress_bar, render_list, render_metrics, render_placeholder, signal_tone, status_tone, to_dict


def render_sentiment_panel(result: Any) -> None:
    sentiment = to_dict(to_dict(result).get("sentiment_context"))
    if not sentiment:
        render_placeholder("Sentiment Context", "not_available")
        return

    st.markdown(f"### Sentiment Context {badge(sentiment.get('status'), status_tone(sentiment.get('status')))}", unsafe_allow_html=True)
    render_metrics(
        [
            metric("Label", sentiment.get("sentiment_label"), tone=signal_tone(sentiment.get("sentiment_label"))),
            metric("Score", sentiment.get("sentiment_score"), tone="info"),
            metric("Source", sentiment.get("source"), tone="neutral"),
        ],
        columns=3,
    )
    st.markdown(progress_bar(sentiment.get("sentiment_score")), unsafe_allow_html=True)
    with st.expander("Context & caveat", expanded=False):
        st.markdown(render_list(sentiment.get("context", []) + sentiment.get("notes", []), "Sentiment belum tersedia."), unsafe_allow_html=True)
