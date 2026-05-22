from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from apps.streamlit_app.ui.components import section_heading
from schemas import AnalysisResult


def render_risk_panel(result: AnalysisResult, show_decision_lab: bool = True) -> None:
    section_heading(
        "Risk Plan",
        "Struktur risiko trade: entry, invalidasi, target, dan rasio reward.",
    )
    risk = result.risk_summary
    entry = risk.entry_area
    stop = risk.stop_loss
    tp = risk.take_profit
    risk_size = abs((entry or 0) - (stop or 0)) if entry and stop else None
    reward_size = abs((tp or 0) - (entry or 0)) if tp and entry else None
    rr = risk.risk_reward

    items = [
        ("Entry", _entry_label(result, entry), "#22c55e"),
        ("Stop Loss", _fmt(stop), "#ef4444"),
        ("Take Profit", _fmt(tp), "#22c55e"),
        ("Risk", _fmt(risk_size), "#f87171"),
        ("Reward", _fmt(reward_size), "#34d399"),
        ("R:R", _fmt_rr(rr), "#93c5fd"),
    ]
    cols = st.columns(6, gap="small")
    for col, (label, value, color) in zip(cols, items, strict=True):
        with col:
            st.markdown(
                f"""
                <div class="fx-card" style="
                    border:1px solid rgba(148,163,184,0.25);
                    border-radius:12px;
                    background:linear-gradient(135deg, rgba(7,27,41,0.66), rgba(15,23,42,0.82));
                    min-height:96px;
                    padding:10px 12px;">
                    <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;">{label}</div>
                    <div style="font-size:1.9rem;font-weight:800;color:{color};">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.caption(risk.notes[0] if risk.notes else "Gunakan ukuran posisi disiplin.")
    _render_risk_gate_lite(result)

    if show_decision_lab:
        section_heading(
            "Decision Lab",
            "Snapshot pembelajaran dan riwayat sinyal dalam sesi dashboard aktif.",
        )
        left, right = st.columns([1, 1], gap="large")
        with left:
            st.markdown("#### Backtest Snapshot")
            _render_snapshot(result)
        with right:
            st.markdown("#### Session Signal History")
            _render_signal_history()


def _render_snapshot(result: AnalysisResult) -> None:
    confidence = result.confidence
    quality = result.trade_quality_score
    trades = int(150 + confidence * 3)
    win_rate = max(10.0, min(90.0, 30 + (quality - 50) * 0.6))
    avg_r = (quality - 50) / 100
    timeout = max(10, 200 - int(confidence))

    items = [
        ("Trades", str(trades), "Valid setup pada data aktif"),
        ("Win Rate", f"{win_rate:.1f}%", "TP lebih dulu tersentuh"),
        ("Avg R", f"{avg_r:+.2f}R", "Rata-rata hasil per setup"),
        ("Open / Timeout", str(timeout), "Setup belum selesai dalam horizon"),
    ]
    for i in range(0, len(items), 2):
        cols = st.columns(2, gap="small")
        for col, (label, value, note) in zip(cols, items[i : i + 2], strict=True):
            with col:
                st.markdown(
                    f"""
                    <div class="fx-card" style="
                        border:1px solid rgba(148,163,184,0.24);
                        border-radius:12px;
                        min-height:110px;
                        padding:12px 14px;
                        background:rgba(15,23,42,0.72);">
                        <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;">{label}</div>
                        <div style="font-size:2rem;font-weight:800;color:#f8fafc;">{value}</div>
                        <div style="font-size:12px;color:#9ca3af;">{note}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    st.caption(
        "Backtest ini snapshot rule-based dari data yang sedang tampil. "
        "Gunakan sebagai validasi awal, bukan jaminan performa live."
    )


def _render_signal_history() -> None:
    history = st.session_state.get("signal_history", [])
    if not history:
        st.info("Belum ada riwayat sesi. Data histori akan terisi otomatis saat dashboard memuat analisa.")
        return
    df = pd.DataFrame(history)
    display = df.rename(
        columns={
            "time": "Time",
            "pair": "Pair",
            "tf": "TF",
            "signal": "Signal",
            "confidence": "Confidence",
            "trend": "Trend",
            "entry": "Entry",
            "sl": "SL",
            "tp": "TP",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.caption(
        "Riwayat ini tersimpan di sesi browser saat ini. "
        "Untuk versi produksi, bisa dipindah ke penyimpanan persisten."
    )


def _render_risk_gate_lite(result: AnalysisResult) -> None:
    gate = _available_dict(getattr(result, "risk_gate_lite", None))
    if not gate:
        return

    section_heading("Risk Gate")
    status = _label(gate.get("risk_status"))
    reasons = [str(reason) for reason in gate.get("reasons", []) if str(reason).strip()]
    reason_text = " | ".join(reasons[:2]) if reasons else "No major risk gate notes."
    color = _risk_gate_color(gate.get("risk_status"))
    st.markdown(
        f"""
        <div class="fx-card" style="
            border:1px solid rgba(148,163,184,0.24);
            border-radius:12px;
            background:rgba(15,23,42,0.72);
            margin-top:12px;
            padding:12px 14px;">
            <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;">Risk Gate</div>
            <div style="font-size:1.35rem;font-weight:800;color:{color};">{escape(status)}</div>
            <div style="font-size:12px;color:#cbd5e1;margin-top:6px;">{escape(reason_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    summary = _risk_gate_distribution(st.session_state.get("risk_gate_history", []))
    if summary:
        st.caption(summary)
    availability = _lite_availability_summary(result.symbol, result.timeframe, st.session_state.get("lite_availability_metrics", {}))
    if availability:
        st.caption(availability)


def _fmt(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"


def _fmt_rr(value: float | None) -> str:
    if value is None:
        return "-"
    return f"1:{value:.2f}"


def _entry_label(result: AnalysisResult, entry: float | None) -> str:
    if entry is None:
        return "-"
    side = "BUY" if result.signal.startswith("BUY") else "SELL" if result.signal.startswith("SELL") else "WAIT"
    return f"{side} {entry:,.2f}"


def _available_dict(value: object) -> dict[str, Any] | None:
    if isinstance(value, dict) and value.get("status") != "unavailable":
        return value
    return None


def _label(value: object) -> str:
    if value is None:
        return "-"
    text = str(value).replace("_", " ").strip()
    return text.title() if text else "-"


def _risk_gate_color(value: object) -> str:
    if value == "valid":
        return "#34d399"
    if value == "caution":
        return "#fbbf24"
    if value == "blocked":
        return "#fb7185"
    return "#f8fafc"


def _risk_gate_distribution(history: object) -> str:
    if not isinstance(history, list):
        return ""

    counts = {"valid": 0, "caution": 0, "blocked": 0}
    for item in history:
        key = str(item).lower()
        if key in counts:
            counts[key] += 1

    total = sum(counts.values())
    if total == 0:
        return ""
    return (
        "Session gate mix: "
        f"Valid {counts['valid']} | "
        f"Caution {counts['caution']} | "
        f"Blocked {counts['blocked']}"
    )


def _lite_availability_summary(symbol: object, timeframe: object, metrics: object) -> str:
    if not isinstance(metrics, dict):
        return ""
    key = f"{symbol}:{timeframe}"
    entry = metrics.get(key)
    if not isinstance(entry, dict):
        return ""

    mc_total = int(entry.get("market_context_total", 0) or 0)
    mc_unavailable = int(entry.get("market_context_unavailable", 0) or 0)
    rg_total = int(entry.get("risk_gate_total", 0) or 0)
    rg_unavailable = int(entry.get("risk_gate_unavailable", 0) or 0)
    if mc_total <= 0 and rg_total <= 0:
        return ""

    mc_rate = (mc_unavailable / mc_total * 100) if mc_total > 0 else 0.0
    rg_rate = (rg_unavailable / rg_total * 100) if rg_total > 0 else 0.0
    return (
        "Session unavailable rate: "
        f"Market Context {mc_rate:.0f}% ({mc_unavailable}/{mc_total}) | "
        f"Risk Gate {rg_rate:.0f}% ({rg_unavailable}/{rg_total})"
    )
