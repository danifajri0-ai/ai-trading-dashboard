from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from apps.streamlit_app.ui.components._shared import (
    badge,
    contribution_bar,
    fmt_value,
    render_placeholder,
    section_title,
    status_tone,
    to_dict,
)


def render_heatmap_panel(result: Any) -> None:
    render_signal_heatmap(result)


def render_signal_heatmap(result: Any) -> None:
    confidence = to_dict(to_dict(result).get("confidence_breakdown"))
    if not confidence:
        render_placeholder("Signal Heatmap", "not_available", "Signal heatmap needs confidence breakdown data from the current analysis.")
        return

    rows = []
    for name, item in to_dict(confidence.get("components")).items():
        details = to_dict(item)
        rows.append({"Component": name, "Score": details.get("score"), "Weight": details.get("weight"), "Weighted": details.get("weighted_score")})
    overall = _safe_float(confidence.get("overall_score"))
    grade = _grade(overall)
    section_title("Signal Heatmap", eyebrow="Contribution Bars", meta="Readable score contribution by engine")
    st.markdown(
        f"""
        <div class="cockpit-heat-summary">
          <div>{badge(confidence.get('status'), status_tone(confidence.get('status')))}</div>
          <div><span>Overall Score</span><strong>{escape(fmt_value(overall, '%', default='Limited data'))}</strong></div>
          <div><span>Grade</span><strong>{escape(grade)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if rows:
        st.markdown("".join(_heat_row(row) for row in rows), unsafe_allow_html=True)
        with st.expander("Raw heatmap table", expanded=False):
            st.dataframe(pd.DataFrame(_display_rows(rows)), use_container_width=True, hide_index=True)
    else:
        render_placeholder("Signal Heatmap", "limited", "Confidence contribution detail is limited for this analysis.")


def _heat_row(row: dict[str, Any]) -> str:
    score = _safe_float(row.get("Score"))
    weight = _safe_float(row.get("Weight"))
    weighted = _safe_float(row.get("Weighted"))
    max_weighted = weight * 100.0 if weight is not None else None
    contribution_pct = (weighted / max_weighted * 100.0) if weighted is not None and max_weighted else 0.0
    return f"""
    <div class="cockpit-heat-row">
      <div>
        <span>Component</span>
        <strong>{escape(_component_label(row.get("Component")))}</strong>
      </div>
      <div>
        <span>Weighted Contribution</span>
        {contribution_bar(contribution_pct)}
      </div>
      <div>
        <span>Score</span>
        <strong>{escape(fmt_value(score))}</strong>
      </div>
      <div>
        <span>Weight</span>
        <strong>{escape(f"{weight:.0%}" if weight is not None else "Limited data")}</strong>
      </div>
      <div>
        <span>Weighted</span>
        <strong>{escape(fmt_value(weighted))}</strong>
      </div>
    </div>
    """


def _safe_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _component_label(value: object) -> str:
    labels = {
        "legacy_confidence": "Technical Confidence",
        "signal_validation": "Signal Validation",
        "data_quality": "Data Quality",
        "risk_gate": "Risk Gate",
    }
    text = str(value or "limited")
    return labels.get(text, fmt_value(text))


def _display_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "Component": _component_label(row.get("Component")),
            "Score": row.get("Score"),
            "Weight": row.get("Weight"),
            "Weighted Contribution": row.get("Weighted"),
        }
        for row in rows
    ]


def _grade(score: float | None) -> str:
    if score is None:
        return "Limited data"
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "D"
