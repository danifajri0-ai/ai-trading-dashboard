from __future__ import annotations

from dataclasses import asdict, is_dataclass
from html import escape
from typing import Any

import streamlit as st


FRIENDLY_LABELS = {
    "not_available": "Currently unavailable",
    "unavailable": "Currently unavailable",
    "limited": "Limited data",
    "partial": "Limited data",
    "available": "Available",
    "caution": "Caution",
    "warning": "Caution",
    "valid": "Valid",
    "blocked": "Blocked",
    "failed": "Failed",
    "standby": "Standby",
    "selective": "Selective execution",
    "ready": "Ready",
    "not_valid": "Not valid",
    "legacy_confidence": "Technical Confidence",
    "signal_validation": "Signal Validation",
    "data_quality": "Data Quality",
    "risk_gate": "Risk Gate",
}


def to_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value):
        return asdict(value)
    return {}


def status_tone(status: object) -> str:
    normalized = str(status or "").lower()
    if normalized in {"available", "valid", "ok"}:
        return "good"
    if normalized in {"caution", "partial", "limited", "warning"}:
        return "warn"
    if normalized in {"blocked", "not_available", "unavailable", "failed"}:
        return "bad"
    return "neutral"


def risk_tone(value: object) -> str:
    normalized = str(value or "").lower()
    if normalized in {"low", "valid", "pass", "passed", "ready"}:
        return "good"
    if normalized in {"medium", "caution", "warning", "partial", "limited", "selective", "standby"}:
        return "warn"
    if normalized in {"high", "extreme", "blocked", "failed", "not_available", "unavailable"}:
        return "bad"
    return "neutral"


def signal_tone(value: object) -> str:
    text = str(value or "").upper()
    if text.startswith("BUY") or text in {"BULLISH", "POSITIVE"}:
        return "good"
    if text.startswith("SELL") or text in {"BEARISH", "NEGATIVE"}:
        return "bad"
    if text in {"WAIT", "NEUTRAL", "MIXED"}:
        return "warn"
    return "neutral"


def fmt_value(value: object, suffix: str = "", default: str = "-") -> str:
    if value is None:
        return default
    if isinstance(value, float):
        return f"{value:,.2f}{suffix}"
    if isinstance(value, int):
        return f"{value:,}{suffix}"
    text = str(value)
    return f"{FRIENDLY_LABELS.get(text.lower(), text)}{suffix}"


def pct(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, number))


def badge(label: object, tone: str = "neutral") -> str:
    return f"<span class='cockpit-badge tone-{escape(tone)}'>{escape(fmt_value(label))}</span>"


def status_chip(label: str, value: object, tone: str = "neutral", note: str | None = None) -> str:
    note_html = f"<small>{escape(note)}</small>" if note else ""
    return (
        f"<div class='cockpit-chip tone-{escape(tone)}'>"
        f"<span>{escape(label)}</span><strong>{escape(fmt_value(value))}</strong>{note_html}"
        "</div>"
    )


def metric(label: str, value: object, note: str | None = None, tone: str = "neutral") -> str:
    note_html = f"<div class='cockpit-note'>{escape(note)}</div>" if note else ""
    return (
        f"<div class='cockpit-metric tone-{escape(tone)}'>"
        f"<span class='cockpit-label'>{escape(label)}</span>"
        f"<span class='cockpit-value'>{escape(fmt_value(value))}</span>"
        f"{note_html}"
        "</div>"
    )


def progress_bar(value: object) -> str:
    width = pct(value)
    return f"<div class='cockpit-bar'><div class='cockpit-fill' style='width:{width:.0f}%'></div></div>"


def contribution_bar(value: object, tone: str = "info") -> str:
    width = pct(value)
    return (
        f"<div class='cockpit-contribution tone-{escape(tone)}'>"
        f"<div class='cockpit-contribution-fill' style='width:{width:.0f}%'></div>"
        "</div>"
    )


def card(title: str, subtitle: str | None = None, body: str = "") -> None:
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"<div class='cockpit-card'><h3>{escape(title)}</h3>{subtitle_html}{body}</div>",
        unsafe_allow_html=True,
    )


def section_title(title: str, eyebrow: str | None = None, meta: str | None = None) -> None:
    eyebrow_html = f"<span>{escape(eyebrow)}</span>" if eyebrow else ""
    meta_html = f"<em>{escape(meta)}</em>" if meta else ""
    st.markdown(
        f"""
        <div class="cockpit-section-title">
          <div>{eyebrow_html}<strong>{escape(title)}</strong></div>
          {meta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(cards: list[str], columns: int = 3) -> None:
    class_name = "two" if columns == 2 else "three" if columns == 3 else ""
    st.markdown(
        f"<div class='cockpit-grid {class_name}'>{''.join(cards)}</div>",
        unsafe_allow_html=True,
    )


def render_placeholder(title: str, status: object, note: str | None = None) -> None:
    text = note or "Data is currently unavailable for this analysis."
    body = f"{badge(status or 'not_available', status_tone(status))}<div class='cockpit-note'>{escape(text)}</div>"
    card(title, body=body)


def render_list(items: list[object], empty: str = "Tidak ada item.") -> str:
    values = [str(item) for item in items if item]
    if not values:
        values = [empty]
    return "<div class='cockpit-list'>" + "".join(
        f"<div class='cockpit-list-item'>{escape(item)}</div>" for item in values
    ) + "</div>"


def dataframe_from_mapping(mapping: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in mapping.items():
        row = {"Key": key}
        if isinstance(value, dict):
            row.update(value)
        else:
            row["Value"] = value
        rows.append(row)
    return rows
