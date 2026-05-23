from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from apps.streamlit_app.ui.components._shared import (
    badge,
    fmt_value,
    metric,
    progress_bar,
    render_list,
    render_placeholder,
    risk_tone,
    section_title,
    status_tone,
    to_dict,
)


def render_cockpit_risk_panel(result: Any) -> None:
    render_risk_execution_console(result)


def render_risk_execution_console(result: Any) -> None:
    risk = to_dict(to_dict(result).get("risk_plan"))
    gate = to_dict(to_dict(result).get("risk_gate"))
    if not risk:
        render_placeholder("Risk Plan", "not_available")
        return

    section_title("Risk Execution Console", eyebrow="Execution Guardrails", meta="Entry, stop, target, R:R, and gate state")
    st.markdown(_risk_console(risk, gate), unsafe_allow_html=True)
    with st.expander("Risk notes", expanded=True):
        st.markdown(
            "<div class='cockpit-risk-notes'>"
            + render_list(risk.get("notes", []) + gate.get("reasons", []), "No risk notes available for this setup.")
            + "</div>",
            unsafe_allow_html=True,
        )


def _risk_console(risk: dict[str, Any], gate: dict[str, Any]) -> str:
    rr = _rr_progress(risk.get("risk_reward"))
    max_risk = risk.get("max_risk_pct")
    max_risk_label = f"{float(max_risk) * 100:.2f}%" if isinstance(max_risk, (int, float)) else "not_available"
    return f"""
    <div class="cockpit-risk-rail">
      <div class="cockpit-risk-grid">
        {metric("Entry Area", risk.get("entry_area"), tone="neutral")}
        {metric("Stop Loss", risk.get("stop_loss"), tone="bad")}
        {metric("Take Profit", risk.get("take_profit"), tone="good")}
      </div>
      <div class="cockpit-risk-profile">
        <div class="cockpit-label">Risk Reward Profile</div>
        <div class="cockpit-value">{escape(fmt_value(risk.get("risk_reward")))} R</div>
        {progress_bar(rr)}
        <div class="cockpit-rr-labels"><span>poor</span><span>tradable</span><span>premium</span></div>
      </div>
      <div class="cockpit-risk-gate-grid">
        {metric("Risk Gate", gate.get("risk_status") or gate.get("status") or "not_available", tone=risk_tone(gate.get("risk_status")))}
        {metric("Max Risk", max_risk_label, tone=risk_tone(risk.get("risk_level")))}
        {metric("Risk Level", risk.get("risk_level"), tone=risk_tone(risk.get("risk_level")))}
      </div>
      <div style="margin-top:10px">
        {badge(risk.get("status"), status_tone(risk.get("status")))}
        {badge(gate.get("risk_status") or gate.get("status") or "not_available", risk_tone(gate.get("risk_status")))}
      </div>
    </div>
    """


def _rr_progress(value: object) -> float:
    try:
        rr = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, (rr / 3.0) * 100.0))
