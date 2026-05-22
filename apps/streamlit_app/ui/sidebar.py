from __future__ import annotations

import streamlit as st


def render_sidebar(symbols: list[str], timeframes: list[str]) -> tuple[str, str]:
    st.session_state.setdefault("show_radar", True)
    st.session_state.setdefault("show_decision_lab", True)
    st.session_state.setdefault("density_mode", "Comfort")
    st.session_state.setdefault("refresh_interval_label", "No Interval")
    st.session_state.setdefault("radar_pair_limit", 3)
    with st.sidebar:
        st.markdown("### Market Setup")
        st.caption("Pilih instrumen dan timeframe untuk dianalisa.")
        symbol = st.selectbox("Symbol", symbols, index=symbols.index("BTCUSD") if "BTCUSD" in symbols else 0)
        timeframe = st.selectbox("Timeframe", timeframes, index=timeframes.index("H1") if "H1" in timeframes else 0)
        st.markdown("### Display")
        st.session_state["show_radar"] = st.toggle("Show Market Radar", value=st.session_state["show_radar"])
        st.session_state["radar_pair_limit"] = st.selectbox(
            "Radar Pair Count",
            [3, 6],
            index=0 if int(st.session_state.get("radar_pair_limit", 3)) == 3 else 1,
        )
        st.session_state["show_decision_lab"] = st.toggle(
            "Show Decision Lab",
            value=st.session_state["show_decision_lab"],
        )
        st.session_state["density_mode"] = st.selectbox(
            "Density",
            ["Comfort", "Compact"],
            index=0 if st.session_state["density_mode"] == "Comfort" else 1,
        )
        st.session_state["refresh_interval_label"] = st.selectbox(
            "Refresh Interval",
            ["No Interval", "5s", "10s", "15s", "30s", "60s", "120s"],
            index=["No Interval", "5s", "10s", "15s", "30s", "60s", "120s"].index(
                st.session_state["refresh_interval_label"]
            )
            if st.session_state["refresh_interval_label"] in {"No Interval", "5s", "10s", "15s", "30s", "60s", "120s"}
            else 0,
        )
        st.markdown("---")
        st.caption("Data akan dianalisa otomatis saat app dibuka atau saat parameter diubah.")
    return symbol, timeframe
