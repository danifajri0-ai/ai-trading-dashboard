from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from apps.streamlit_app.ui.components._shared import (
    badge,
    fmt_value,
    risk_tone,
    signal_tone,
    status_chip,
    status_tone,
    to_dict,
)


def render_trading_desk_header(result: Any, source: str = "local") -> None:
    render_command_header(result, source=source)


def render_command_header(result: Any, source: str = "local") -> None:
    payload = to_dict(result)
    overview = to_dict(payload.get("market_overview"))
    price = to_dict(payload.get("price_snapshot"))
    signal_decision = to_dict(payload.get("signal_decision"))
    data_quality = to_dict(payload.get("data_quality"))
    risk_gate = to_dict(payload.get("risk_gate"))
    signal = overview.get("signal", "-")
    bias = overview.get("bias", "-")
    status = overview.get("status", "not_available")
    last_price = fmt_value(price.get("last_price"))
    updated_at = price.get("updated_at") or "no timestamp"
    validation = signal_decision.get("validation_score")
    confidence = overview.get("confidence")
    data_status = data_quality.get("status") or price.get("status") or "not_available"
    gate_status = risk_gate.get("risk_status") or risk_gate.get("status") or "not_available"
    provider = price.get("price_source") or source

    st.markdown(
        f"""
        <div class="cockpit-shell">
          <div class="cockpit-header">
            <div class="cockpit-command-header">
              <div>
                <div class="cockpit-kicker">Trading Desk Command Header</div>
                <div class="cockpit-title">{escape(str(payload.get("symbol", "-")))} / {escape(str(payload.get("timeframe", "-")))}</div>
                <div class="cockpit-price">{escape(last_price)}</div>
                <div class="cockpit-subtitle">
                  Provider: {escape(fmt_value(provider))} | Updated: {escape(str(updated_at))} | Profile: Rich Cockpit v2
                </div>
                <div style="margin-top:12px">
                  {badge(signal, signal_tone(signal))}
                  {badge(bias, signal_tone(bias))}
                  {badge(status, status_tone(status))}
                </div>
              </div>
              <div class="cockpit-command-grid">
                {status_chip("Signal", signal, signal_tone(signal))}
                {status_chip("Bias", bias, signal_tone(bias))}
                {status_chip("Confidence", _compact_percent(confidence), "info", "baseline")}
                {status_chip("Validation", _compact_percent(validation, default="limited"), status_tone(signal_decision.get("status")), "baseline")}
                {status_chip("Data Quality", _compact_percent(data_quality.get("score"), default=data_status), status_tone(data_status), "baseline")}
                {status_chip("Risk Gate", gate_status, risk_tone(gate_status))}
                {status_chip("Price Feed", price.get("status") or "not_available", status_tone(price.get("status")))}
                {status_chip("Source", source, "neutral")}
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _compact_percent(value: object, default: object = "not_available") -> str:
    try:
        return f"{float(value):.0f}%"
    except (TypeError, ValueError):
        return fmt_value(default)
