from __future__ import annotations

import streamlit as st

from schemas import AnalysisResult


def render_warning_panel(result: AnalysisResult) -> None:
    _render_data_health(result)

    st.subheader("Risk Warnings")
    if result.warnings:
        for warning in result.warnings:
            st.warning(warning)
    else:
        st.success("Tidak ada warning kritis pada setup saat ini.")

    st.markdown(
        """
        <div style="
            border:1px solid rgba(59,130,246,0.25);
            border-radius:10px;
            background:rgba(30,64,175,0.25);
            color:#60a5fa;
            padding:16px;
            margin-top:14px;">
            Dashboard ini memakai data publik dan berfungsi sebagai decision-support, bukan sinyal
            eksekusi otomatis. Selalu validasi harga, spread, berita besar, dan manajemen risiko
            melalui broker sebelum mengambil posisi.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.caption("AI Trading Dashboard (TM)")
    st.caption("Muhammad Alfazry Ramadhani 2026. All rights reserved.")
    st.caption(
        "Hak paten dan hak milik dilindungi. "
        "Trademark notice: identitas produk untuk penggunaan internal dashboard trading."
    )


def _render_data_health(result: AnalysisResult) -> None:
    data_health = getattr(result, "data_health_lite", None)
    if not isinstance(data_health, dict):
        return

    status = str(data_health.get("status", "")).strip().lower()
    if status in {"", "unavailable"}:
        return

    st.subheader("Data Health")
    fresh = data_health.get("data_is_fresh")
    freshness = "Fresh" if fresh is True else "Not Fresh" if fresh is False else "Unknown"
    missing = "Yes" if bool(data_health.get("missing_candle_detected")) else "No"
    duplicate = "Yes" if bool(data_health.get("duplicate_candle_detected")) else "No"
    last_candle = str(data_health.get("last_candle_time") or "-")
    warnings = [str(item) for item in data_health.get("warnings", []) if str(item).strip()]

    col1, col2, col3, col4 = st.columns(4, gap="small")
    col1.metric("Freshness", freshness)
    col2.metric("Missing Candle", missing)
    col3.metric("Duplicate Candle", duplicate)
    col4.metric("Last Candle", last_candle)
    if warnings:
        st.caption(" | ".join(warnings[:2]))
