from __future__ import annotations

from html import escape

import streamlit as st


def section_panel(title: str, subtitle: str | None = None, content: str | None = None) -> None:
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    content_html = content or ""
    st.markdown(
        f"""
        <section class="terminal-panel">
          <div class="terminal-panel-head">
            <h2>{escape(title)}</h2>
            {subtitle_html}
          </div>
          {content_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def section_heading(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="section-heading">
          <h2>{escape(title)}</h2>
          {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(
    label: str,
    value: str,
    sub: str | None = None,
    tone: str | None = None,
    compact: bool = False,
) -> str:
    sub_html = f"<div class='metric-sub'>{escape(sub)}</div>" if sub else ""
    compact_class = " metric-card-compact" if compact else ""
    tone_class = _tone_class(tone)
    return (
        f"<div class='metric-card{compact_class} {tone_class}'>"
        f"<div class='metric-label'>{escape(label)}</div>"
        f"<div class='metric-value'>{escape(value)}</div>"
        f"{sub_html}"
        "</div>"
    )


def status_pill(label: str, value: str, tone: str | None = None) -> str:
    tone_class = _tone_class(tone)
    return (
        f"<div class='status-pill {tone_class}'>"
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(value)}</strong>"
        "</div>"
    )


def render_grid(cards: list[str], columns: int = 4) -> str:
    column_class = f"grid-{max(1, min(columns, 6))}"
    return f"<div class='metric-grid terminal-grid {column_class}'>{''.join(cards)}</div>"


def _tone_class(tone: str | None) -> str:
    if tone in {"good", "warn", "bad", "info", "neutral"}:
        return f"tone-{tone}"
    return "tone-neutral"
