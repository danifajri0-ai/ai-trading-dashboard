from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from apps.streamlit_app.ui.components._shared import (
    badge,
    fmt_value,
    metric,
    progress_bar,
    risk_tone,
    signal_tone,
    status_tone,
    to_dict,
)
from apps.streamlit_app.ui.utils import delta_from_reference, readiness_label, safe_float


def render_chart_zone_panel(result: Any) -> None:
    render_pro_chart_zone(result)


def render_pro_chart_zone(result: Any) -> None:
    render_pro_chart(result)
    render_post_chart_summary(result)


def render_pro_chart(result: Any) -> None:
    payload = to_dict(result)
    price = to_dict(payload.get("price_snapshot"))
    overview = to_dict(payload.get("market_overview"))
    risk = to_dict(payload.get("risk_plan"))
    gate = to_dict(payload.get("risk_gate"))
    structure = to_dict(payload.get("market_structure"))
    data_quality = to_dict(payload.get("data_quality"))

    st.markdown(_chart_card(payload, price, overview, risk, gate, structure, data_quality), unsafe_allow_html=True)


def render_post_chart_summary(result: Any) -> None:
    payload = to_dict(result)
    overview = to_dict(payload.get("market_overview"))
    signal = to_dict(payload.get("signal_decision"))
    risk = to_dict(payload.get("risk_plan"))
    gate = to_dict(payload.get("risk_gate"))
    execution_mode = _execution_mode(signal, gate)
    cards = [
        _trade_brief(signal, overview, risk, gate, execution_mode),
        _risk_snapshot(risk, gate),
        _setup_checklist(signal, risk, gate, execution_mode),
    ]

    st.markdown(
        "<div class='cockpit-post-chart-grid'>"
        + "".join(card.strip() for card in cards)
        + "</div>",
        unsafe_allow_html=True,
    )


def render_live_trade_brief(
    signal: dict[str, Any],
    overview: dict[str, Any],
    risk: dict[str, Any],
    gate: dict[str, Any],
    execution_mode: str,
) -> None:
    st.markdown(_trade_brief(signal, overview, risk, gate, execution_mode), unsafe_allow_html=True)


def _chart_card(
    payload: dict[str, Any],
    price: dict[str, Any],
    overview: dict[str, Any],
    risk: dict[str, Any],
    gate: dict[str, Any],
    structure: dict[str, Any],
    data_quality: dict[str, Any],
) -> str:
    current = safe_float(price.get("last_price"))
    support = safe_float(structure.get("support"))
    resistance = safe_float(structure.get("resistance"))
    entry = safe_float(risk.get("entry_area"))
    stop = safe_float(risk.get("stop_loss"))
    target = safe_float(risk.get("take_profit"))
    levels = [value for value in (support, stop, current, entry, target, resistance) if value is not None]
    chart_status = "available" if current is not None and len(levels) >= 2 else "limited"
    low, high = _level_range(levels)
    direction = _direction(overview, signal_tone(overview.get("signal") or overview.get("bias")))
    price_move = _delta_badge(current, entry, "Price Move")

    return f"""
    <div class="cockpit-chart-card">
      <div class="cockpit-chart-head">
        <div>
          <span>Decision Map</span>
          <strong>{escape(fmt_value(payload.get("symbol")))} / {escape(fmt_value(payload.get("timeframe")))}</strong>
        </div>
        <div>
          {badge(chart_status, status_tone(chart_status))}
          {badge(overview.get("bias") or "Limited data", signal_tone(overview.get("bias")))}
        </div>
      </div>
      <div class="cockpit-chart-toolbar">
        {badge(f"Signal: {fmt_value(overview.get('signal') or 'limited')}", signal_tone(overview.get("signal")))}
        {badge(f"Bias: {fmt_value(overview.get('bias') or 'limited')}", signal_tone(overview.get("bias")))}
        {badge(f"Risk Gate: {fmt_value(gate.get('risk_status') or gate.get('status') or 'limited')}", risk_tone(gate.get("risk_status")))}
        {badge(f"Data Quality: {fmt_value(data_quality.get('status') or 'limited')}", status_tone(data_quality.get("status")))}
      </div>
      <div class="cockpit-chart-price-row">
        <div>
          <div class="cockpit-chart-price">{escape(fmt_value(current, default="Limited data"))}</div>
          {price_move}
        </div>
        <div class="cockpit-direction tone-{escape(direction['tone'])}">
          <span>{escape(direction['label'])}</span>
          <strong>{escape(direction['arrow'])}</strong>
        </div>
      </div>
      <div class="cockpit-chart-subtitle">
        Decision map uses available price, support, resistance, entry, stop, and target levels.
      </div>
      <div class="cockpit-price-map">
        {_signal_zone(entry, stop, target, low, high)}
        {_level_marker("Resistance", resistance, low, high, "bad", "resistance")}
        {_level_marker("Target", target, low, high, "good", "target")}
        {_level_marker("Entry Zone", entry, low, high, "info", "entry")}
        {_level_marker("Current Price", current, low, high, "neutral", "current")}
        {_level_marker("Stop Loss", stop, low, high, "bad", "stop")}
        {_level_marker("Support", support, low, high, "good", "support")}
        <div class="cockpit-chart-gridline"></div>
      </div>
      <div class="cockpit-distance-grid">
        {_distance_tile("Distance to Entry", current, entry)}
        {_distance_tile("Distance to Stop", current, stop)}
        {_distance_tile("Distance to Target", current, target)}
      </div>
    </div>
    """


def _trade_brief(
    signal: dict[str, Any],
    overview: dict[str, Any],
    risk: dict[str, Any],
    gate: dict[str, Any],
    execution_mode: str,
) -> str:
    invalidation = _invalidation_condition(signal, risk)
    checklist = [
        ("Entry", risk.get("entry_area") if risk.get("entry_area") is not None else "limited"),
        ("Stop Loss", risk.get("stop_loss") if risk.get("stop_loss") is not None else "limited"),
        ("Take Profit", risk.get("take_profit") if risk.get("take_profit") is not None else "limited"),
        ("R:R", risk.get("risk_reward") if risk.get("risk_reward") is not None else "limited"),
        ("Trade Readiness", readiness_label(overview.get("trade_quality_score"))),
        ("Risk Gate", gate.get("risk_status") or gate.get("status") or "limited"),
    ]
    next_action = _next_best_action(execution_mode, signal, gate)
    return f"""
    <div class="cockpit-summary-card cockpit-brief-card">
      <div class="cockpit-brief-title">
        <span>Live Trade Brief</span>
        <strong>{escape(fmt_value(signal.get("action") or overview.get("signal") or "limited"))}</strong>
      </div>
      <div class="cockpit-readiness-gauge">
        <div><span>Trade Readiness</span><strong>{escape(readiness_label(overview.get("trade_quality_score")))}</strong></div>
        {progress_bar(overview.get("trade_quality_score"))}
      </div>
      <div class="cockpit-brief-grid">
        {"".join(_brief_item(label, value) for label, value in checklist)}
      </div>
      <div class="cockpit-brief-checklist">
        <strong>Setup Checklist</strong>
        {_check_item("Next Action", next_action, risk_tone(execution_mode))}
        {_check_item("Invalidation", invalidation, risk_tone(gate.get("risk_status")))}
      </div>
    </div>
    """


def _risk_snapshot(risk: dict[str, Any], gate: dict[str, Any]) -> str:
    max_risk = risk.get("max_risk_pct")
    max_risk_label = f"{float(max_risk) * 100:.0f}%" if isinstance(max_risk, (int, float)) else "limited"
    return f"""
    <div class="cockpit-summary-card">
      <div class="cockpit-brief-title">
        <span>Risk Snapshot</span>
        <strong>{escape(fmt_value(gate.get("risk_status") or gate.get("status") or "limited"))}</strong>
      </div>
      <div class="cockpit-summary-grid">
        {metric("Entry", risk.get("entry_area") if risk.get("entry_area") is not None else "limited", tone="neutral")}
        {metric("Stop", risk.get("stop_loss") if risk.get("stop_loss") is not None else "limited", tone="bad")}
        {metric("Target", risk.get("take_profit") if risk.get("take_profit") is not None else "limited", tone="good")}
        {metric("R:R", risk.get("risk_reward") if risk.get("risk_reward") is not None else "limited", tone="info")}
        {metric("Max Risk", max_risk_label, tone=risk_tone(risk.get("risk_level")))}
        {metric("Risk Level", risk.get("risk_level") or "limited", tone=risk_tone(risk.get("risk_level")))}
      </div>
    </div>
    """


def _setup_checklist(signal: dict[str, Any], risk: dict[str, Any], gate: dict[str, Any], execution_mode: str) -> str:
    invalidation = _invalidation_condition(signal, risk)
    return f"""
    <div class="cockpit-summary-card">
      <div class="cockpit-brief-title">
        <span>Setup Checklist</span>
        <strong>{escape(fmt_value(execution_mode))}</strong>
      </div>
      <div class="cockpit-brief-checklist summary-only">
        {_check_item("Execution", execution_mode, risk_tone(execution_mode))}
        {_check_item("Risk Gate", gate.get("risk_status") or gate.get("status") or "limited", risk_tone(gate.get("risk_status")))}
        {_check_item("Validation", signal.get("status") or "limited", status_tone(signal.get("status")))}
        {_check_item("Invalidation", invalidation, risk_tone(gate.get("risk_status")))}
      </div>
    </div>
    """


def _brief_item(label: str, value: object) -> str:
    tone = signal_tone(value) if label in {"Signal", "Bias"} else risk_tone(value)
    return metric(label, value, tone=tone)


def _check_item(label: str, value: object, tone: str) -> str:
    return (
        f"<div class='cockpit-check-item tone-{escape(tone)}'>"
        f"<span>{escape(label)}</span><strong>{escape(fmt_value(value, default='Limited data'))}</strong>"
        "</div>"
    )


def _level_marker(label: str, value: float | None, low: float, high: float, tone: str, kind: str) -> str:
    if value is None or high <= low:
        return ""
    top = 100.0 - (((value - low) / (high - low)) * 100.0)
    top = max(4.0, min(96.0, top))
    return (
        f"<div class='cockpit-level-marker level-{escape(kind)} tone-{escape(tone)}' style='top:{top:.2f}%'>"
        f"<span>{escape(label)}</span><strong>{escape(fmt_value(value))}</strong>"
        "</div>"
    )


def _signal_zone(entry: float | None, stop: float | None, target: float | None, low: float, high: float) -> str:
    if entry is None or high <= low:
        return ""
    zone_values = [value for value in (entry, stop, target) if value is not None]
    if len(zone_values) < 2:
        return ""
    zone_top = 100.0 - (((max(zone_values) - low) / (high - low)) * 100.0)
    zone_bottom = 100.0 - (((min(zone_values) - low) / (high - low)) * 100.0)
    top = max(4.0, min(96.0, zone_top))
    height = max(10.0, min(92.0, zone_bottom - zone_top))
    return f"<div class='cockpit-signal-zone' style='top:{top:.2f}%;height:{height:.2f}%'><span>Signal Zone</span></div>"


def _distance_tile(label: str, current: float | None, target: float | None) -> str:
    delta = delta_from_reference(target, current)
    if delta is None:
        return (
            "<div class='cockpit-distance-tile tone-neutral'>"
            f"<span>{escape(label)}</span><strong>baseline</strong>"
            "</div>"
        )
    arrow = _display_arrow(delta["arrow"])
    return (
        f"<div class='cockpit-distance-tile tone-{escape(delta['tone'])}'>"
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(arrow)} {escape(delta['points'])} / {escape(delta['percent'])}</strong>"
        "</div>"
    )


def _level_range(levels: list[float]) -> tuple[float, float]:
    if not levels:
        return 0.0, 1.0
    low = min(levels)
    high = max(levels)
    if high == low:
        spread = abs(high) * 0.01 or 1.0
        return low - spread, high + spread
    padding = (high - low) * 0.12
    return low - padding, high + padding


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


def _direction(overview: dict[str, Any], fallback_tone: str) -> dict[str, str]:
    signal = str(overview.get("signal") or "").upper()
    bias = str(overview.get("bias") or "").upper()
    if signal.startswith("BUY") or bias == "BULLISH":
        return {"arrow": "↑", "label": "Upside map", "tone": "good"}
    if signal.startswith("SELL") or bias == "BEARISH":
        return {"arrow": "↓", "label": "Downside map", "tone": "bad"}
    tone = fallback_tone if fallback_tone in {"good", "bad", "neutral"} else "neutral"
    return {"arrow": "→", "label": "Sideways map", "tone": tone}


def _delta_badge(current: float | None, reference: float | None, label: str) -> str:
    delta = delta_from_reference(current, reference)
    if delta is None:
        return f"<div class='cockpit-delta tone-neutral'><span>{escape(label)}</span><strong>baseline</strong></div>"
    return (
        f"<div class='cockpit-delta tone-{escape(delta['tone'])}'>"
        f"<span>{escape(label)}</span><strong>{escape(_display_arrow(delta['arrow']))} {escape(delta['points'])} / {escape(delta['percent'])}</strong>"
        "</div>"
    )


def _display_arrow(value: str) -> str:
    if value == "up":
        return "↑"
    if value == "down":
        return "↓"
    return "→"


def _next_best_action(execution_mode: str, signal: dict[str, Any], gate: dict[str, Any]) -> str:
    if execution_mode == "blocked":
        return "Stand down until blockers clear."
    if execution_mode == "standby":
        return "Wait for a cleaner trigger."
    if execution_mode == "selective":
        return "Reduce size and require confirmation."
    if signal.get("valid_signal") is True and str(gate.get("risk_status") or "").lower() == "valid":
        return "Monitor entry zone."
    return "Keep setup on watchlist."


def _invalidation_condition(signal: dict[str, Any], risk: dict[str, Any]) -> str:
    stop_loss = risk.get("stop_loss")
    action = str(signal.get("action") or "").upper()
    if stop_loss is not None and action.startswith(("BUY", "SELL")):
        return f"Price breaches stop area {fmt_value(stop_loss)}"
    if signal.get("blocked_reason"):
        return str(signal["blocked_reason"])
    if signal.get("warning_reason"):
        return str(signal["warning_reason"])
    return "Limited data"
