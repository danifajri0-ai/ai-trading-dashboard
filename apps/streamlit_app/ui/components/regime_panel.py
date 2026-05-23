from __future__ import annotations

from typing import Any

import streamlit as st

from apps.streamlit_app.ui.components._shared import badge, metric, progress_bar, render_list, render_metrics, render_placeholder, status_tone, to_dict


def render_regime_panel(result: Any) -> None:
    regime = to_dict(to_dict(result).get("regime_analysis"))
    structure = to_dict(to_dict(result).get("market_structure"))
    if not regime:
        render_placeholder("Regime Analysis", "not_available")
        return

    st.markdown(f"### Regime & Structure {badge(regime.get('status'), status_tone(regime.get('status')))}", unsafe_allow_html=True)
    render_metrics(
        [
            metric("Regime", regime.get("regime"), tone=status_tone(regime.get("status"))),
            metric("Score", regime.get("regime_score"), tone="info"),
            metric("Strategy", regime.get("preferred_strategy"), tone="neutral"),
            metric("Structure", structure.get("structure"), tone=status_tone(structure.get("status"))),
        ],
        columns=4,
    )
    st.markdown(progress_bar(regime.get("regime_score")), unsafe_allow_html=True)
    with st.expander("Regime notes", expanded=False):
        st.markdown(render_list(regime.get("notes", []) + structure.get("notes", []), "Belum ada catatan."), unsafe_allow_html=True)
