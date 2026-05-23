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
    render_metrics,
    render_placeholder,
    risk_tone,
    section_title,
    signal_tone,
    status_tone,
    to_dict,
)


def render_signal_decision_panel(result: Any) -> None:
    render_signal_command_center(result)


def render_signal_command_center(result: Any) -> None:
    payload = to_dict(result)
    signal = to_dict(payload.get("signal_decision"))
    if not signal:
        render_placeholder("Signal Decision", "not_available")
        return
    overview = to_dict(payload.get("market_overview"))
    risk = to_dict(payload.get("risk_plan"))
    gate = to_dict(payload.get("risk_gate"))
    execution_mode = _execution_mode(signal, gate)

    section_title("Signal Command Center", eyebrow="Decision Layer", meta="Primary action, validation, and execution readiness")
    st.markdown(
        f"""
        <div class="cockpit-decision-layout">
          <div class="cockpit-decision-block">
            <div class="cockpit-label">Primary Action</div>
            <div class="cockpit-decision-hero tone-{escape(signal_tone(signal.get('action')))}">{escape(fmt_value(signal.get('action')))}</div>
            {badge(signal.get('status'), status_tone(signal.get('status')))}
            {badge(execution_mode, risk_tone(execution_mode))}
            <div class="cockpit-note">Bias: {escape(fmt_value(signal.get('bias')))} | Gate: {escape(fmt_value(gate.get('risk_status') or gate.get('status') or 'not_available'))}</div>
            {progress_bar(signal.get("validation_score") or signal.get("confidence"))}
          </div>
          <div class="cockpit-decision-block">
            <div class="cockpit-grid two">
              {metric("Execution Mode", execution_mode, tone=risk_tone(execution_mode))}
              {metric("Trade Quality", overview.get("trade_quality_score"), tone="info")}
            </div>
            <div class="cockpit-signal-checklist">
              {_signal_check_item("Confirmation Reason", signal.get("confirmation_reason") or "Limited data", status_tone(signal.get("status")))}
              {_signal_check_item("Warning", signal.get("warning_reason") or "No active warning", "warn" if signal.get("warning_reason") else "neutral")}
              {_signal_check_item("Blocker", signal.get("blocked_reason") or "No active blocker", "bad" if signal.get("blocked_reason") else "neutral")}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_metrics(
        [
            metric("Execution Mode", execution_mode, tone=risk_tone(execution_mode)),
            metric("Trade Quality", overview.get("trade_quality_score"), tone="info"),
            metric("Valid Signal", _valid_label(signal.get("valid_signal")), tone=status_tone(signal.get("status"))),
        ],
        columns=3,
    )
    with st.expander("Why this signal", expanded=True):
        st.markdown(render_list(signal.get("reasons", []), "Belum ada rationale."), unsafe_allow_html=True)
    st.markdown(_compact_decision_grid(signal, risk, gate), unsafe_allow_html=True)
    if signal.get("notes"):
        with st.expander("Decision notes", expanded=False):
            st.markdown(render_list(signal.get("notes", []), "Tidak ada catatan tambahan."), unsafe_allow_html=True)


def _execution_mode(signal: dict[str, Any], gate: dict[str, Any]) -> str:
    action = str(signal.get("action") or "").upper()
    gate_status = str(gate.get("risk_status") or "").lower()
    if gate_status == "blocked":
        return "blocked"
    if action in {"WAIT", "AVOID_HIGH_RISK"}:
        return "standby"
    if gate_status == "caution" or signal.get("warning_reason"):
        return "selective"
    if signal.get("valid_signal") is True:
        return "ready"
    return "limited"


def _valid_label(value: object) -> str:
    if value is True:
        return "valid"
    if value is False:
        return "not_valid"
    return "limited"


def _confirmation_needed(signal: dict[str, Any]) -> str:
    if signal.get("blocked_reason"):
        return str(signal["blocked_reason"])
    if signal.get("warning_reason"):
        return str(signal["warning_reason"])
    if signal.get("confirmation_reason"):
        return str(signal["confirmation_reason"])
    return "not_available"


def _compact_decision_grid(signal: dict[str, Any], risk: dict[str, Any], gate: dict[str, Any]) -> str:
    return (
        "<div class='cockpit-signal-mini-grid'>"
        + _signal_check_item("Confirmation", _confirmation_needed(signal), status_tone(signal.get("status")))
        + _signal_check_item("Invalidation", _invalidation_condition(signal, risk), risk_tone(gate.get("risk_status")))
        + _signal_check_item("Risk Gate", gate.get("risk_status") or gate.get("status") or "not_available", risk_tone(gate.get("risk_status")))
        + "</div>"
    )


def _signal_check_item(label: str, value: object, tone: str) -> str:
    return (
        f"<div class='cockpit-signal-check tone-{escape(tone)}'>"
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(_short_text(fmt_value(value, default='Limited data')))}</strong>"
        "</div>"
    )


def _short_text(value: str) -> str:
    if len(value) <= 110:
        return value
    return value[:107].rstrip() + "..."


def _invalidation_condition(signal: dict[str, Any], risk: dict[str, Any]) -> str:
    stop_loss = risk.get("stop_loss")
    action = str(signal.get("action") or "").upper()
    if stop_loss is not None and action.startswith(("BUY", "SELL")):
        return f"Invalid if price breaches stop area {fmt_value(stop_loss)}."
    if signal.get("blocked_reason"):
        return str(signal["blocked_reason"])
    if signal.get("warning_reason"):
        return str(signal["warning_reason"])
    return "not_available"
