from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from apps.streamlit_app.ui.components._shared import badge, fmt_value, render_placeholder, section_title, status_tone, to_dict


def render_evidence_panel(result: Any) -> None:
    render_evidence_layer(result)


def render_evidence_layer(result: Any) -> None:
    evidence = to_dict(to_dict(result).get("evidence_layer"))
    if not evidence:
        render_placeholder("Evidence Layer", "not_available")
        return

    section_title("Evidence Layer", eyebrow="Visual Evidence Cards", meta="Technical, risk, data quality, and contradictions")
    st.markdown(
        "<div class='cockpit-note'>"
        f"{badge(evidence.get('status'), status_tone(evidence.get('status')))} "
        "Evidence is grouped for fast trade review; open the raw table only when you need audit detail."
        "</div>",
        unsafe_allow_html=True,
    )
    groups = {
        "Technical Evidence": evidence.get("technical_evidence", []),
        "Risk Evidence": evidence.get("risk_evidence", []),
        "Data Quality Evidence": evidence.get("data_quality_evidence", []),
        "Contradictions": evidence.get("contradictions", []),
    }
    st.markdown(
        "<div class='cockpit-evidence-grid'>"
        + "".join(_evidence_card(title, rows) for title, rows in groups.items())
        + "</div>",
        unsafe_allow_html=True,
    )
    with st.expander("Raw evidence table", expanded=False):
        tabs = st.tabs(list(groups.keys()))
        for tab, (title, rows) in zip(tabs, groups.items()):
            with tab:
                clean_rows = [row for row in rows if isinstance(row, dict)]
                if clean_rows:
                    st.dataframe(pd.DataFrame(_display_rows(clean_rows)), use_container_width=True, hide_index=True)
                else:
                    st.info(f"{title}: currently unavailable for this analysis.")


def _evidence_card(title: str, rows: object) -> str:
    clean_rows = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    if not clean_rows:
        clean_rows = [{"label": "Limited data", "status": "limited", "detail": _empty_copy(title), "score": None}]
    status = _group_status(clean_rows)
    preview_rows = clean_rows[:3]
    return (
        "<div class='cockpit-evidence-card'>"
        f"<div class='topline'><h4>{escape(title)}</h4>{badge(status, status_tone(status))}</div>"
        f"<p>{_group_summary(title, clean_rows)}</p>"
        + "".join(_evidence_item(row) for row in preview_rows)
        + ("<p>More items available in raw table.</p>" if len(clean_rows) > 3 else "")
        + "</div>"
    )


def _evidence_item(row: dict[str, Any]) -> str:
    status = row.get("status") or "not_available"
    score = row.get("score")
    score_text = f" | Score {fmt_value(score)}" if score is not None else ""
    return (
        "<div class='cockpit-evidence-item'>"
        f"<strong>{escape(_friendly_evidence_label(row.get('label') or 'Evidence'))} {badge(status, status_tone(status))}</strong>"
        f"<small>{escape(fmt_value(row.get('detail'), default='No detail'))}{escape(score_text)}</small>"
        "</div>"
    )


def _group_status(rows: list[dict[str, Any]]) -> str:
    statuses = {str(row.get("status") or "not_available") for row in rows}
    if statuses == {"available"}:
        return "available"
    if "caution" in statuses or "not_available" in statuses:
        return "caution"
    return next(iter(statuses), "not_available")


def _empty_copy(title: str) -> str:
    if title == "Contradictions":
        return "No contradiction is currently exposed for this analysis."
    return "This evidence group is currently limited for this analysis."


def _group_summary(title: str, rows: list[dict[str, Any]]) -> str:
    if len(rows) == 1 and str(rows[0].get("label", "")).lower() == "limited data":
        return _empty_copy(title)
    if title == "Contradictions":
        return f"{len(rows)} caution item(s) to check before execution."
    return f"{len(rows)} evidence item(s) available for trade review."


def _display_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    display_rows = []
    for row in rows:
        display_rows.append(
            {
                "Label": _friendly_evidence_label(row.get("label")),
                "Status": fmt_value(row.get("status")),
                "Detail": fmt_value(row.get("detail"), default="No detail"),
                "Score": row.get("score"),
            }
        )
    return display_rows


def _friendly_evidence_label(value: object) -> str:
    labels = {
        "Legacy analysis reason": "Technical reason",
        "Legacy warning": "Trading warning",
        "Final confidence": "Final Confidence",
        "Signal validation": "Signal Validation",
        "Risk gate": "Risk Gate",
        "Data quality": "Data Quality",
        "Signal contradiction": "Signal Contradiction",
        "Signal blocker": "Signal Blocker",
    }
    text = str(value or "Evidence")
    return labels.get(text, fmt_value(text))
