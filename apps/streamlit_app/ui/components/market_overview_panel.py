from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from apps.streamlit_app.ui.components._shared import (
    badge,
    fmt_value,
    render_placeholder,
    risk_tone,
    section_title,
    signal_tone,
    status_tone,
    to_dict,
)
from apps.streamlit_app.ui.utils import safe_float, score_grade


def render_market_overview_panel(result: Any) -> None:
    render_market_state_strip(result)


def render_market_state_strip(result: Any) -> None:
    payload = to_dict(result)
    overview = to_dict(payload.get("market_overview"))
    if not overview:
        render_placeholder("Market Overview", "not_available")
        return
    signal = to_dict(payload.get("signal_decision"))
    regime = to_dict(payload.get("regime_analysis"))
    data_quality = to_dict(payload.get("data_quality"))
    risk_gate = to_dict(payload.get("risk_gate"))

    section_title(
        "Market State Board",
        eyebrow="Market Overview",
        meta=str(overview.get("summary") or "Live market state from cockpit schema"),
    )
    st.markdown(_market_state_strip(overview, signal, regime, data_quality, risk_gate), unsafe_allow_html=True)
    st.markdown(
        f"<div class='cockpit-note'>{escape(str(overview.get('summary') or 'Ringkasan market belum tersedia.'))} "
        f"{badge(overview.get('status'), status_tone(overview.get('status')))}</div>",
        unsafe_allow_html=True,
    )


def _market_state_strip(
    overview: dict[str, Any],
    signal: dict[str, Any],
    regime: dict[str, Any],
    data_quality: dict[str, Any],
    risk_gate: dict[str, Any],
) -> str:
    confidence = safe_float(overview.get("confidence"))
    trend_note = _trend_interpretation(overview.get("bias"), confidence)
    momentum_status = "limited"
    momentum_value = _momentum_value(signal)
    momentum_note = _momentum_note(signal)
    volatility_value = regime.get("volatility_state") or "not_available"
    volatility_status = regime.get("status") or "not_available"
    execution_value = overview.get("trade_quality_score")
    execution_note = _execution_note(execution_value, risk_gate)
    cards = [
        _state_card(
            "Trend Pressure",
            _trend_read(overview).upper(),
            overview.get("status"),
            trend_note,
            signal_tone(overview.get("bias")),
            "wide",
        ),
        _state_card("Momentum", str(momentum_value).upper(), momentum_status, momentum_note, status_tone(momentum_status), "wide"),
        _state_card("Volatility", _volatility_value(volatility_value), volatility_status, _volatility_note(volatility_value), status_tone(volatility_status), "compact"),
        _state_card(
            "Execution Quality",
            f"{score_grade(execution_value)} GRADE" if execution_value is not None else "Limited data",
            risk_gate.get("risk_status") or risk_gate.get("status") or "not_available",
            str(execution_note),
            risk_tone(risk_gate.get("risk_status")),
            "compact",
        ),
        _state_card("Data Health", _data_usability(data_quality).upper(), data_quality.get("status") or "not_available", _data_health_note(data_quality), status_tone(data_quality.get("status")), "compact"),
    ]
    return "<div class='cockpit-state-board'>" + "".join(cards) + "</div>"


def _state_card(title: str, value: object, status: object, note: object, tone: str, size: str) -> str:
    return (
        f"<div class='cockpit-state-card state-{escape(size)} tone-{escape(tone)}'>"
        f"<div class='topline'><h4>{escape(title)}</h4>{badge(status or 'not_available', status_tone(status))}</div>"
        f"<span class='value'>{escape(fmt_value(value))}</span>"
        "<div class='cockpit-delta tone-neutral'><span>Delta</span><strong>baseline</strong></div>"
        f"<p>{escape(str(note or 'No detail available.'))}</p>"
        "</div>"
    )


def _trend_read(overview: dict[str, Any]) -> str:
    bias = str(overview.get("bias") or "limited").upper()
    confidence = safe_float(overview.get("confidence"))
    if confidence is None:
        return f"{bias} pressure"
    if confidence >= 70:
        return f"{bias} pressure"
    if confidence >= 50:
        return f"{bias} but selective"
    return "Mixed pressure"


def _trend_interpretation(bias: object, confidence: float | None) -> str:
    text = str(bias or "").upper()
    if confidence is None:
        return "Directional pressure is limited because confidence is not exposed."
    if text in {"BULLISH", "BEARISH"} and confidence >= 70:
        return "Directional pressure is strong enough to prioritize aligned setups."
    if text in {"BULLISH", "BEARISH"}:
        return "Directional pressure exists, but entries should wait for confirmation."
    return "No dominant pressure; treat this as a range or wait environment."


def _momentum_value(signal: dict[str, Any]) -> str:
    if signal.get("confirmation_reason"):
        return "confirmation present"
    if signal.get("warning_reason"):
        return "needs confirmation"
    return "Limited data"


def _volatility_value(value: object) -> str:
    text = str(value or "").upper()
    if not text or text == "NOT_AVAILABLE":
        return "LIMITED DATA"
    if "CALM" in text or "LOW" in text:
        return "CALM"
    if "HIGH" in text or "VOLATILE" in text:
        return "VOLATILE"
    return text


def _momentum_note(signal: dict[str, Any]) -> str:
    if signal.get("confirmation_reason"):
        return str(signal["confirmation_reason"])
    if signal.get("warning_reason"):
        return str(signal["warning_reason"])
    return "Momentum detail is limited in the current analysis result."


def _volatility_note(value: object) -> str:
    text = str(value or "").lower()
    if "high" in text or "volatile" in text:
        return "Tradable only with reduced size and wider invalidation."
    if "low" in text:
        return "Movement may be slow; avoid chasing weak breaks."
    if text and text != "not_available":
        return "Volatility context is available for execution filtering."
    return "Volatility context is currently unavailable."


def _execution_note(score: object, risk_gate: dict[str, Any]) -> str:
    grade = score_grade(score)
    gate = risk_gate.get("risk_status") or risk_gate.get("status")
    return f"{grade} setup quality with {fmt_value(gate, default='Limited data')} gate state."


def _data_usability(data_quality: dict[str, Any]) -> str:
    status = str(data_quality.get("status") or "not_available").lower()
    if status == "available":
        return "Usable"
    if status in {"caution", "partial", "limited"}:
        return "Use with caution"
    return "Limited data"


def _data_health_note(data_quality: dict[str, Any]) -> str:
    issues = data_quality.get("issues")
    if isinstance(issues, list) and issues:
        return "; ".join(str(item) for item in issues[:2])
    status = str(data_quality.get("status") or "not_available").lower()
    if status == "available":
        return "Data is usable for this cockpit view."
    return "Data is limited; treat the setup as lower confidence."
