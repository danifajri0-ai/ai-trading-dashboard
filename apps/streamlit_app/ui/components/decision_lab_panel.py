from __future__ import annotations

from typing import Any

import streamlit as st

from apps.streamlit_app.ui.components._shared import badge, metric, render_list, render_metrics, render_placeholder, status_tone, to_dict


def render_decision_lab_panel(result: Any) -> None:
    signal = to_dict(to_dict(result).get("signal_decision"))
    risk = to_dict(to_dict(result).get("risk_gate"))
    data_quality = to_dict(to_dict(result).get("data_quality"))
    if not signal:
        render_placeholder("Decision Lab", "not_available")
        return

    valid = signal.get("valid_signal")
    readiness = "Ready" if valid and risk.get("risk_status") == "valid" else "Wait / Review"
    st.markdown(f"### Decision Lab {badge(readiness, 'good' if readiness == 'Ready' else 'warn')}", unsafe_allow_html=True)
    render_metrics(
        [
            metric("Action", signal.get("action"), tone="info"),
            metric("Signal Valid", valid, tone="good" if valid else "warn"),
            metric("Risk Gate", risk.get("risk_status"), tone=status_tone(risk.get("risk_status"))),
            metric("Data", data_quality.get("status"), tone=status_tone(data_quality.get("status"))),
        ],
        columns=4,
    )
    notes = [
        signal.get("blocked_reason"),
        signal.get("warning_reason"),
        signal.get("confirmation_reason"),
    ]
    st.markdown(render_list([note for note in notes if note], "Decision lab menunggu input validasi."), unsafe_allow_html=True)
