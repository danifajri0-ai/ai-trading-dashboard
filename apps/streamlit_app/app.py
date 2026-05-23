from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:  # pragma: no cover - optional dependency
    st_autorefresh = None

# Ensure project root is importable when Streamlit runs this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from apps.streamlit_app.client.api_client import ApiClientError, analyze_market_http, get_symbols
from apps.streamlit_app.ui import (
    render_chart_panel,
    render_market_table,
    render_risk_panel,
    render_sidebar,
    render_signal_card,
    render_warning_panel,
)
from apps.streamlit_app.ui.cockpit_renderer import render_cockpit
from config import SETTINGS
from schemas import AnalysisResult, CockpitAnalysisResult
from services.analysis_service import analyze_market
from services.cockpit_service import analyze_cockpit_market
from services.market_data_service import get_market_data, get_supported_symbols, get_supported_timeframes


st.set_page_config(page_title="AI Trading Dashboard", layout="wide")


def main() -> None:
    _render_styles()

    symbols, timeframes = _load_market_options_cached()
    symbol, timeframe = render_sidebar(symbols=symbols, timeframes=timeframes)
    use_cockpit_v2 = st.sidebar.toggle("Rich Cockpit v2", value=True)
    show_radar = bool(st.session_state.get("show_radar", True))
    radar_pair_limit = int(st.session_state.get("radar_pair_limit", 3))
    show_decision_lab = bool(st.session_state.get("show_decision_lab", True))
    _apply_auto_refresh(st.session_state.get("refresh_interval_label", "No Interval"))

    try:
        with st.spinner("Menganalisis market cockpit..."):
            if use_cockpit_v2:
                cockpit_result, analysis_source = _analyze_cockpit(symbol, timeframe)
                result = cockpit_result.legacy_result
                radar_rows = []
                st.session_state["last_cockpit_result"] = cockpit_result
                st.session_state["last_result"] = result
                st.session_state["last_market_frame"] = pd.DataFrame()
                st.session_state["last_radar"] = radar_rows
                st.session_state["last_analysis_source"] = analysis_source
                _append_signal_history(result)
                _append_lite_availability_metrics(result)
                _render_source_banner(analysis_source)
                render_cockpit(cockpit_result, source=analysis_source)
                return

            result, analysis_source = _analyze_market(symbol, timeframe)
            market_frame = get_market_data(symbol, timeframe)
            radar_rows = _build_market_radar(symbols, timeframe, result, radar_pair_limit) if show_radar else []
        st.session_state["last_result"] = result
        st.session_state["last_market_frame"] = market_frame
        st.session_state["last_radar"] = radar_rows
        st.session_state["last_analysis_source"] = analysis_source
        _append_signal_history(result)
        _append_lite_availability_metrics(result)
        _render_source_banner(analysis_source)
        _render_dashboard(
            result,
            market_frame,
            radar_rows,
            show_radar=show_radar,
            show_decision_lab=show_decision_lab,
        )
    except Exception:
        st.error(
            "Maaf, analisa belum bisa ditampilkan sekarang. "
            "Coba beberapa saat lagi atau gunakan kombinasi symbol/timeframe lain."
        )


def _render_dashboard(
    result: AnalysisResult,
    market_frame: pd.DataFrame,
    radar_rows: list[dict[str, str]] | None = None,
    show_radar: bool = True,
    show_decision_lab: bool = True,
) -> None:
    render_signal_card(result, market_frame)
    render_chart_panel(result, market_frame)
    render_risk_panel(result, show_decision_lab=show_decision_lab)
    render_market_table(result, market_frame, radar_rows or [], show_radar=show_radar)
    render_warning_panel(result)


def _append_signal_history(result: AnalysisResult) -> None:
    history = st.session_state.setdefault("signal_history", [])
    history.insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pair": result.symbol,
            "tf": result.timeframe,
            "signal": result.signal,
            "confidence": f"{result.confidence:.0f}%",
            "trend": result.bias,
            "entry": _fmt_optional(result.risk_summary.entry_area),
            "sl": _fmt_optional(result.risk_summary.stop_loss),
            "tp": _fmt_optional(result.risk_summary.take_profit),
        },
    )
    st.session_state["signal_history"] = history[:25]
    _append_risk_gate_history(result)


def _append_risk_gate_history(result: AnalysisResult) -> None:
    status = _risk_gate_status(result)
    if status is None:
        return
    history = st.session_state.setdefault("risk_gate_history", [])
    history.insert(0, status)
    st.session_state["risk_gate_history"] = history[:50]


def _risk_gate_status(result: AnalysisResult) -> str | None:
    gate = getattr(result, "risk_gate_lite", None)
    if not isinstance(gate, dict) or gate.get("status") == "unavailable":
        return None
    risk_status = gate.get("risk_status")
    return str(risk_status) if risk_status else None


def _append_lite_availability_metrics(result: AnalysisResult) -> None:
    key = f"{result.symbol}:{result.timeframe}"
    metrics = st.session_state.setdefault("lite_availability_metrics", {})
    entry = metrics.setdefault(
        key,
        {
            "market_context_total": 0,
            "market_context_unavailable": 0,
            "risk_gate_total": 0,
            "risk_gate_unavailable": 0,
        },
    )
    market_context_status = _lite_status(getattr(result, "market_context_lite", None))
    risk_gate_status = _lite_status(getattr(result, "risk_gate_lite", None))

    entry["market_context_total"] += 1
    if market_context_status == "unavailable":
        entry["market_context_unavailable"] += 1
    entry["risk_gate_total"] += 1
    if risk_gate_status == "unavailable":
        entry["risk_gate_unavailable"] += 1

    metrics[key] = entry
    st.session_state["lite_availability_metrics"] = metrics


def _lite_status(value: object) -> str:
    if isinstance(value, dict):
        status = value.get("status")
        if isinstance(status, str):
            return status
    return "unavailable"


def _build_market_radar(
    symbols: list[str],
    timeframe: str,
    primary_result: AnalysisResult,
    max_pairs: int = 3,
) -> list[dict[str, str]]:
    pair_order = [primary_result.symbol, *[s for s in symbols if s != primary_result.symbol]]
    selected_pairs = pair_order[: max(1, max_pairs)]
    rows = [_radar_row(primary_result)]
    for symbol in selected_pairs[1:]:
        analyzed = _analyze_market_quiet_cached(symbol, timeframe)
        if analyzed is None:
            rows.append(
                {
                    "Pair": _pair_label(symbol),
                    "Signal": "WAIT",
                    "Confidence": "-",
                    "Trend": "WAIT",
                    "Price": "-",
                    "Move %": "-",
                    "Freshness": "Unavailable",
                    "Last Candle": "-",
                    "Risk": "high",
                    "Quality": "0",
                }
            )
            continue
        rows.append(_radar_row(analyzed))
    return rows


def _radar_row(result: AnalysisResult) -> dict[str, str]:
    close_proxy = (result.technical_summary.ema_fast + result.technical_summary.ema_slow) / 2
    return {
        "Pair": _pair_label(result.symbol),
        "Signal": result.signal,
        "Confidence": f"{result.confidence:.0f}%",
        "Trend": _trend_from_bias(result.bias),
        "Price": f"{close_proxy:,.2f}",
        "Move %": _move_pct_label(result),
        "Freshness": "Fresh",
        "Last Candle": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Risk": result.risk_level,
        "Quality": f"{result.trade_quality_score:.0f}",
    }


def _analyze_market_quiet(symbol: str, timeframe: str) -> AnalysisResult | None:
    if SETTINGS.mode == "http_api":
        try:
            return analyze_market_http(symbol, timeframe)
        except ApiClientError:
            pass
        except Exception:
            pass
    try:
        return analyze_market(symbol, timeframe)
    except Exception:
        return None


def _analyze_market_quiet_cached(symbol: str, timeframe: str) -> AnalysisResult | None:
    cache = st.session_state.setdefault("radar_analysis_cache", {})
    key = (symbol, timeframe)
    cached = cache.get(key)
    if isinstance(cached, AnalysisResult):
        return cached

    analyzed = _analyze_market_quiet(symbol, timeframe)
    if isinstance(analyzed, AnalysisResult):
        cache[key] = analyzed
        st.session_state["radar_analysis_cache"] = cache
    return analyzed


def _fmt_optional(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"


def _pair_label(symbol: str) -> str:
    if symbol.endswith("USD") and len(symbol) > 3:
        return f"{symbol[:-3]}/USD"
    return symbol


def _trend_from_bias(bias: str) -> str:
    if bias == "BULLISH":
        return "BUY"
    if bias == "BEARISH":
        return "SELL"
    return "WAIT"


def _move_pct_label(result: AnalysisResult) -> str:
    magnitude = max(0.05, min(1.25, result.confidence / 100))
    if result.signal.startswith("BUY"):
        return f"UP +{magnitude:.2f}%"
    if result.signal.startswith("SELL"):
        return f"DOWN -{magnitude:.2f}%"
    return f"FLAT +{magnitude * 0.2:.2f}%"


def _load_market_options() -> tuple[list[str], list[str]]:
    if SETTINGS.mode == "http_api":
        try:
            payload = get_symbols()
            return payload["symbols"], payload["timeframes"]
        except ApiClientError:
            pass
    return list(get_supported_symbols()), list(get_supported_timeframes())


def _load_market_options_cached() -> tuple[list[str], list[str]]:
    cached = st.session_state.get("market_options_cache")
    if isinstance(cached, dict):
        symbols = cached.get("symbols")
        timeframes = cached.get("timeframes")
        if isinstance(symbols, list) and isinstance(timeframes, list) and symbols and timeframes:
            return symbols, timeframes

    symbols, timeframes = _load_market_options()
    st.session_state["market_options_cache"] = {"symbols": symbols, "timeframes": timeframes}
    return symbols, timeframes


def _analyze_market(symbol: str, timeframe: str) -> tuple[AnalysisResult, str]:
    if SETTINGS.mode == "http_api":
        try:
            return analyze_market_http(symbol, timeframe), "http_api"
        except ApiClientError:
            return analyze_market(symbol, timeframe), "local_fallback"
    return analyze_market(symbol, timeframe), "local"


def _analyze_cockpit(symbol: str, timeframe: str) -> tuple[CockpitAnalysisResult, str]:
    try:
        return analyze_cockpit_market(symbol, timeframe), "cockpit_service"
    except Exception:
        legacy_result = analyze_market(symbol, timeframe)
        from services.cockpit_service import build_cockpit_result

        return build_cockpit_result(legacy_result), "cockpit_fallback"


def _render_source_banner(source: str) -> None:
    if source == "http_api":
        st.caption("Analysis source: backend API")
        return
    if source == "local_fallback":
        st.warning("API tidak tersedia, analysis menggunakan local fallback.")
        return
    if source == "cockpit_service":
        st.caption("Analysis source: cockpit service")
        return
    if source == "cockpit_fallback":
        st.warning("Cockpit service tidak tersedia penuh, UI memakai fallback schema dari legacy analysis.")
        return
    st.caption("Analysis source: local service")


def _apply_auto_refresh(refresh_label: str) -> None:
    if st_autorefresh is None:
        return
    seconds = _refresh_seconds(refresh_label)
    if seconds is None:
        return
    st_autorefresh(interval=seconds * 1000, key=f"auto_refresh_{seconds}")


def _refresh_seconds(refresh_label: str) -> int | None:
    mapping = {
        "No Interval": None,
        "5s": 5,
        "10s": 10,
        "15s": 15,
        "30s": 30,
        "60s": 60,
        "120s": 120,
    }
    return mapping.get(refresh_label, None)


def _render_styles() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

          @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @keyframes pulseGlow {
            0% { box-shadow: 0 0 0 rgba(56,189,248,0); }
            100% { box-shadow: 0 10px 24px rgba(56,189,248,0.15); }
          }
          .stApp {
            background: linear-gradient(180deg, #07111f 0%, #0a101a 54%, #071016 100%);
            color: #e2e8f0;
            font-family: 'Plus Jakarta Sans', Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          }
          [data-testid="stAppViewContainer"] > .main .block-container {
            max-width: 1480px;
            padding: 1.35rem 1.5rem 2.5rem;
          }
          [data-testid="stSidebar"] {
            background: #0f172a;
            border-right: 1px solid rgba(148,163,184,0.2);
          }
          html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          }
          [data-testid="stDataFrame"] table {
            font-size: 0.93rem;
          }
          [data-testid="stDataFrame"] tbody tr:hover td {
            background-color: rgba(56,189,248,0.12) !important;
            transition: background-color 180ms ease;
          }
          div[data-baseweb="tab-list"] {
            gap: 8px;
            padding: 4px 2px;
          }
          div[data-baseweb="tab"] {
            border-radius: 999px;
            border: 1px solid rgba(148,163,184,0.24);
            background: rgba(15,23,42,0.72);
            transition: all 180ms ease;
          }
          button[role="tab"][aria-selected="true"] {
            border-color: rgba(56,189,248,0.45) !important;
            background: linear-gradient(135deg, rgba(14,116,144,0.25), rgba(30,64,175,0.25)) !important;
            box-shadow: 0 8px 18px rgba(2,132,199,0.18);
          }
          .desk-shell-title {
            display: none;
          }
          .section-marker {
            display: none;
          }
          .fx-card {
            transition: transform 180ms ease, box-shadow 220ms ease, border-color 180ms ease;
            animation: fadeInUp 260ms ease;
          }
          .fx-card:hover {
            transform: translateY(-2px);
            border-color: rgba(56,189,248,0.42) !important;
            box-shadow: 0 10px 22px rgba(2,132,199,0.18);
          }
          .factor-group {
            border: 1px solid rgba(148,163,184,0.24);
            border-radius: 14px;
            background: linear-gradient(135deg, rgba(9,23,43,0.82), rgba(15,23,42,0.88));
            padding: 12px 14px;
            margin-bottom: 10px;
            transition: transform 180ms ease, box-shadow 220ms ease, border-color 180ms ease;
          }
          .factor-group:hover {
            transform: translateY(-2px);
            border-color: rgba(34,211,238,0.45);
            animation: pulseGlow 220ms ease forwards;
          }
          .factor-track {
            width: 100%;
            height: 10px;
            border-radius: 999px;
            background: rgba(2,6,23,0.7);
            overflow: hidden;
          }
          .factor-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #38bdf8, #22c55e);
            transition: width 360ms ease;
          }
          [data-testid="stMetric"] {
            background: rgba(15,23,42,0.72);
            border: 1px solid rgba(148,163,184,0.2);
            border-radius: 10px;
            padding: 10px 12px;
          }
          [data-testid="stDataFrame"] {
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 10px;
          }
          h1, h2, h3 {
            letter-spacing: 0;
            color: #f8fafc;
            font-family: 'Plus Jakarta Sans', Inter, system-ui, sans-serif;
          }
          p {
            color: #cbd5e1;
            font-size: 14px;
            line-height: 1.6;
          }
          .hero-panel,
          .terminal-panel,
          .setup-panel {
            border: 1px solid rgba(148,163,184,0.20);
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(9,22,39,0.96), rgba(10,26,38,0.92));
            box-shadow: 0 24px 70px rgba(0,0,0,0.28);
          }
          .hero-panel {
            background: linear-gradient(180deg, rgba(10, 26, 48, 0.96), rgba(6, 17, 32, 0.98));
            border: 1px solid rgba(56, 189, 248, 0.22);
            border-radius: 28px;
            padding: 28px 32px;
            margin-bottom: 24px;
            box-shadow: 0 24px 70px rgba(0, 0, 0, 0.25);
          }
          .hero-copy {
            max-width: 920px;
          }
          .hero-kicker {
            color: #2dd4bf;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.04em;
            margin-bottom: 6px;
            text-transform: uppercase;
          }
          .hero-copy h1 {
            color: #f8fafc;
            font-size: clamp(40px, 4vw, 48px);
            font-weight: 800;
            line-height: 1;
            margin: 0;
          }
          .hero-copy h2 {
            color: #93c5fd;
            font-size: clamp(28px, 3vw, 36px);
            font-weight: 800;
            line-height: 1.08;
            margin: 8px 0 0;
          }
          .hero-copy p {
            max-width: 720px;
            margin: 12px 0 0;
            color: #cbd5e1;
            font-size: 15px;
          }
          .status-bar {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 12px;
            margin-top: 20px;
            margin-bottom: 24px;
          }
          .status-pill {
            background: rgba(15, 31, 54, 0.85);
            border: 1px solid rgba(96, 165, 250, 0.20);
            border-radius: 16px;
            padding: 12px 14px;
            min-height: 64px;
          }
          .status-pill span,
          .metric-label {
            display: block;
            color: #94a3b8;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.04em;
            line-height: 1.2;
            text-transform: uppercase;
          }
          .status-pill strong {
            display: block;
            color: #f8fafc;
            font-size: 15px;
            font-weight: 800;
            line-height: 1.2;
            margin-top: 7px;
            overflow-wrap: anywhere;
          }
          .hero-subsection {
            margin-top: 24px;
            padding-top: 20px;
            border-top: 1px solid rgba(148,163,184,0.16);
          }
          .subsection-title,
          .hero-subsection-title {
            color: #38BDF8;
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 0.06em;
            margin-bottom: 12px;
            text-transform: uppercase;
          }
          .section-heading {
            margin: 22px 0 12px;
          }
          .section-heading h2,
          .terminal-panel-head h2 {
            color: #f8fafc;
            font-size: 22px;
            font-weight: 800;
            line-height: 1.15;
            margin: 0;
          }
          .section-heading p,
          .terminal-panel-head p {
            color: #94a3b8;
            font-size: 14px;
            margin: 4px 0 0;
          }
          .terminal-panel {
            padding: 24px;
            margin: 18px 0;
          }
          .terminal-panel-head {
            margin-bottom: 14px;
          }
          .metric-grid,
          .terminal-grid {
            display: grid;
            gap: 14px;
          }
          .terminal-grid.grid-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .terminal-grid.grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
          .terminal-grid.grid-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
          .terminal-grid.grid-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }
          .terminal-grid.grid-6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }
          .metric-card {
            background: rgba(10, 25, 47, 0.90);
            border: 1px solid rgba(96, 165, 250, 0.20);
            border-radius: 18px;
            padding: 16px;
            min-height: 88px;
            box-shadow: 0 14px 34px rgba(0,0,0,0.16);
          }
          .metric-card-compact {
            min-height: 86px;
            padding: 14px;
          }
          .metric-value {
            color: #f8fafc;
            font-size: 25px;
            font-weight: 800;
            line-height: 1.08;
            margin-top: 8px;
            overflow-wrap: anywhere;
          }
          .metric-card-compact .metric-value {
            font-size: 21px;
          }
          .metric-sub {
            color: #9ca3af;
            font-size: 12px;
            line-height: 1.35;
            margin-top: 7px;
          }
          .setup-panel {
            display: grid;
            grid-template-columns: minmax(260px, 0.85fr) minmax(0, 2fr);
            gap: 18px;
            padding: 22px;
            margin-bottom: 18px;
          }
          .setup-title {
            font-size: 32px;
            font-weight: 800;
            line-height: 1.05;
            margin-top: 6px;
          }
          .setup-panel p {
            margin: 10px 0 0;
          }
          .tone-good { border-color: rgba(34,197,94,0.34); }
          .tone-good .metric-value,
          .tone-good strong,
          .tone-text-good { color: #34d399; }
          .tone-warn { border-color: rgba(245,158,11,0.34); }
          .tone-warn .metric-value,
          .tone-warn strong,
          .tone-text-warn { color: #fbbf24; }
          .tone-bad { border-color: rgba(239,68,68,0.36); }
          .tone-bad .metric-value,
          .tone-bad strong,
          .tone-text-bad { color: #fb7185; }
          .tone-info { border-color: rgba(56,189,248,0.32); }
          .tone-info .metric-value,
          .tone-info strong,
          .tone-text-info { color: #38bdf8; }
          .tone-neutral .metric-value,
          .tone-neutral strong,
          .tone-text-neutral { color: #f8fafc; }
          .trading-card {
            border: 1px solid rgba(56,189,248,0.20);
            border-radius: 10px;
            background: linear-gradient(135deg, rgba(7,19,43,0.95), rgba(11,32,64,0.82));
            padding: 14px 16px;
          }
          .trading-card h4 {
            margin: 0;
            font-size: 0.82rem;
            color: #7dd3fc;
            text-transform: uppercase;
          }
          .trading-card p {
            margin: 8px 0 0;
            color: #e2e8f0;
            font-size: 1.45rem;
            font-weight: 700;
          }
          @media (max-width: 1180px) {
            .status-bar,
            .terminal-grid.grid-5,
            .terminal-grid.grid-6 {
              grid-template-columns: repeat(3, minmax(0, 1fr));
            }
            .terminal-grid.grid-4 {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .setup-panel {
              grid-template-columns: 1fr;
            }
          }
          @media (max-width: 720px) {
            [data-testid="stAppViewContainer"] > .main .block-container {
              padding-left: 1rem;
              padding-right: 1rem;
            }
            .hero-panel,
            .terminal-panel,
            .setup-panel {
              border-radius: 18px;
              padding: 18px;
            }
            .status-bar,
            .terminal-grid,
            .terminal-grid.grid-2,
            .terminal-grid.grid-3,
            .terminal-grid.grid-4,
            .terminal-grid.grid-5,
            .terminal-grid.grid-6 {
              grid-template-columns: 1fr;
            }
            .hero-copy h1 {
              font-size: 40px;
            }
            .hero-copy h2 {
              font-size: 28px;
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
