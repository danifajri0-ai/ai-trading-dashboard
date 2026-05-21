from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import math
import time

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:  # The app still works; only automatic refresh is disabled.
    st_autorefresh = None

from ai_signal import SignalSummary, build_signal_summary
from market_data import (
    INTERVALS,
    PAIRS,
    MarketDataError,
    MarketRequest,
    compatible_periods,
    data_source_label,
    fetch_market_data,
    get_symbol,
    validate_request,
)
from sentiment_news import build_market_context
from technical_analysis import (
    IndicatorSettings,
    MarketLevels,
    RiskPlan,
    TrendAnalysis,
    add_indicators,
    analyze_trend,
    calculate_levels,
    calculate_risk_plan,
    format_price,
)


st.set_page_config(
    page_title="AI Trading Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


@dataclass(frozen=True)
class RuntimeSettings:
    live_mode: bool
    refresh_mode: str
    refresh_seconds: int
    data_source: str
    show_market_radar: bool
    show_backtest: bool
    show_signal_history: bool


@dataclass(frozen=True)
class PriceMovement:
    direction: str
    arrow: str
    css_class: str
    change: float
    change_percent: float
    label: str


@st.cache_data(ttl=900, show_spinner=False)
def load_market_data(
    symbol: str,
    period: str,
    interval: str,
    refresh_bucket: int,
) -> pd.DataFrame:
    del refresh_bucket
    return fetch_market_data(symbol=symbol, period=period, interval=interval)


@st.cache_data(ttl=600, show_spinner=False)
def load_market_summary(
    label: str,
    symbol: str,
    period: str,
    interval: str,
    settings_values: tuple[int, int, int, int, int, float],
    refresh_bucket: int,
) -> dict[str, object]:
    del refresh_bucket
    settings = IndicatorSettings(
        ema_fast=settings_values[0],
        ema_slow=settings_values[1],
        rsi_window=settings_values[2],
        atr_window=settings_values[3],
        level_window=settings_values[4],
        risk_reward=settings_values[5],
    )
    raw_data = fetch_market_data(symbol=symbol, period=period, interval=interval)
    data = add_indicators(raw_data, settings)
    levels = calculate_levels(data, settings)
    trend = analyze_trend(levels)
    risk_plan = calculate_risk_plan(levels, trend, settings)
    signal = build_signal_summary(levels, trend, risk_plan)
    movement = calculate_price_movement(data)
    freshness = build_freshness_status(data, interval)

    return {
        "Pair": label,
        "Signal": signal.action,
        "Confidence": signal.confidence,
        "Trend": trend.direction,
        "Price": levels.latest_close,
        "Move %": movement.change_percent,
        "Freshness": freshness["status"],
        "Last Candle": freshness["last_candle"],
    }


def main() -> None:
    render_global_styles()

    request, indicator_settings, runtime = render_sidebar()
    arm_auto_refresh(runtime)

    try:
        validate_request(request)
    except MarketDataError as exc:
        st.error(str(exc))
        st.stop()

    refresh_bucket = int(time.time() // runtime.refresh_seconds) if runtime.live_mode else 0

    try:
        raw_data = load_market_data(
            request.symbol,
            request.period,
            request.interval,
            refresh_bucket,
        )
    except MarketDataError as exc:
        st.error(str(exc))
        st.stop()

    try:
        data = add_indicators(raw_data, indicator_settings)
        levels = calculate_levels(data, indicator_settings)
        trend = analyze_trend(levels)
        risk_plan = calculate_risk_plan(levels, trend, indicator_settings)
        signal = build_signal_summary(levels, trend, risk_plan)
        movement = calculate_price_movement(data)
        signal_history = update_signal_history(request, levels, trend, risk_plan, signal, movement)
    except Exception as exc:
        st.error(f"Data berhasil dimuat, tetapi analisis belum bisa dihitung: {exc}")
        st.stop()

    render_section("Header", render_header, request, levels, trend, signal, runtime, len(data), movement)
    render_section("Data Freshness", render_data_freshness, data, request, runtime)
    render_section("Overview", render_status_bar, request, levels, trend, signal, indicator_settings, movement)
    render_section("Best Setup", render_best_setup, request, levels, trend, risk_plan, signal, movement)
    if runtime.show_market_radar:
        render_section("Market Radar", render_market_radar, request, indicator_settings, refresh_bucket)
    render_section("Chart", render_chart, data, request, levels, indicator_settings, runtime)
    render_section("Market Analysis", render_analysis, levels, trend, signal, movement)
    render_section("Risk Plan", render_risk_plan, risk_plan)
    if runtime.show_backtest or runtime.show_signal_history:
        render_section(
            "Decision Lab",
            render_decision_lab,
            data,
            request,
            indicator_settings,
            runtime,
            signal_history,
        )
    render_section("Detailed Trading Information", render_detail_panels, data, levels, trend, risk_plan, signal, indicator_settings, movement)
    render_section("Market Context", render_context, request)
    render_disclaimer()
    render_footer()


def render_section(section_name: str, renderer, *args) -> None:
    try:
        renderer(*args)
    except Exception as exc:
        st.error(f"{section_name} gagal dirender: {exc}")


def render_sidebar() -> tuple[MarketRequest, IndicatorSettings, RuntimeSettings]:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-panel">
                <span>Market Setup</span>
                <p>Pilih market, timeframe, dan rentang data yang ingin dipantau.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected_pair = st.selectbox("Market", list(PAIRS.keys()))
        interval = st.selectbox("Timeframe", list(INTERVALS), index=3)

        allowed_periods = compatible_periods(interval)
        default_period = "1mo" if "1mo" in allowed_periods else allowed_periods[-1]
        period = st.selectbox(
            "Data Range",
            list(allowed_periods),
            index=list(allowed_periods).index(default_period),
        )

        st.markdown(
            """
            <div class="sidebar-panel compact">
                <span>Data Setup</span>
                <p>Atur ritme pembaruan data sesuai gaya monitoring Anda.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        refresh_mode = st.radio(
            "Update Mode",
            ["Smooth Refresh", "Live Monitor", "Manual Review"],
            horizontal=False,
            help="Smooth Refresh menjaga tampilan chart lebih tenang untuk pemantauan rutin. Live Monitor memperbarui lebih cepat.",
        )

        if refresh_mode == "Live Monitor":
            refresh_seconds = st.selectbox("Refresh Interval", [10, 15, 30], index=1)
            live_mode = True
        elif refresh_mode == "Smooth Refresh":
            refresh_seconds = st.selectbox("Refresh Interval", [30, 60, 120, 300], index=1)
            live_mode = True
        else:
            refresh_seconds = 300
            live_mode = False

        st.markdown(
            """
            <div class="sidebar-note">
                Zoom dan posisi chart dipertahankan saat data diperbarui. Data publik dapat memiliki jeda dan perlu divalidasi dengan broker.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sidebar-panel compact">
                <span>Indicator Setup</span>
                <p>Sesuaikan sensitivitas sinyal, area harga, dan rencana risiko.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        ema_fast = st.number_input("Fast EMA", min_value=2, max_value=100, value=20, step=1)
        ema_slow = st.number_input(
            "Slow EMA",
            min_value=int(ema_fast) + 1,
            max_value=300,
            value=max(50, int(ema_fast) + 1),
            step=1,
        )
        rsi_window = st.number_input("RSI Period", min_value=5, max_value=50, value=14, step=1)
        atr_window = st.number_input("ATR Period", min_value=5, max_value=50, value=14, step=1)
        level_window = st.number_input("S/R Lookback Candles", min_value=10, max_value=200, value=30, step=5)
        risk_reward = st.number_input("Risk:Reward Target", min_value=1.0, max_value=5.0, value=2.0, step=0.25)

        st.markdown(
            """
            <div class="sidebar-panel compact">
                <span>Product Tools</span>
                <p>Aktifkan fitur premium-facing untuk validasi, radar market, dan riwayat sinyal.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        show_market_radar = st.toggle("Market Radar", value=True)
        show_backtest = st.toggle("Backtest Snapshot", value=True)
        show_signal_history = st.toggle("Session Signal History", value=True)

        if st.button("Update Market Data", use_container_width=True):
            load_market_data.clear()
            st.rerun()

    request = MarketRequest(
        label=selected_pair,
        symbol=get_symbol(selected_pair),
        period=period,
        interval=interval,
    )
    indicator_settings = IndicatorSettings(
        ema_fast=int(ema_fast),
        ema_slow=int(ema_slow),
        rsi_window=int(rsi_window),
        atr_window=int(atr_window),
        level_window=int(level_window),
        risk_reward=float(risk_reward),
    )
    runtime = RuntimeSettings(
        live_mode=bool(live_mode),
        refresh_mode=refresh_mode,
        refresh_seconds=int(refresh_seconds),
        data_source=data_source_label(get_symbol(selected_pair)),
        show_market_radar=bool(show_market_radar),
        show_backtest=bool(show_backtest),
        show_signal_history=bool(show_signal_history),
    )
    return request, indicator_settings, runtime


def arm_auto_refresh(runtime: RuntimeSettings) -> None:
    if not runtime.live_mode:
        return

    if st_autorefresh is not None:
        st_autorefresh(
            interval=runtime.refresh_seconds * 1000,
            key="market_auto_refresh",
        )
        return

    st.sidebar.warning(
        "Auto-refresh belum aktif karena paket streamlit-autorefresh tidak tersedia. "
        "Gunakan tombol Update Market Data atau install dependency dari requirements.txt."
    )


def render_header(
    request: MarketRequest,
    levels: MarketLevels,
    trend: TrendAnalysis,
    signal: SignalSummary,
    runtime: RuntimeSettings,
    candle_count: int,
    movement: PriceMovement,
) -> None:
    live_status = {
        "Smooth Refresh": "Smooth",
        "Live Monitor": "Live",
        "Manual Review": "Manual",
    }.get(runtime.refresh_mode, runtime.refresh_mode)
    source_label = "Binance / Yahoo" if "Binance" in runtime.data_source else "Yahoo Public"
    refreshed_at = datetime.now().strftime("%H:%M:%S")
    action_class = "buy" if signal.action == "BUY" else "sell" if signal.action == "SELL" else "wait"
    trend_class = "buy" if trend.direction == "BUY" else "sell" if trend.direction == "SELL" else "wait"

    st.markdown(
        f"""
        <section class="terminal-header">
            <div>
                <div class="eyebrow">AI Trading Dashboard</div>
                <h1>{request.label} Trading Desk</h1>
                <p>Pantau arah market, momentum, area harga penting, dan rencana risiko dalam satu tampilan profesional.</p>
            </div>
            <div class="terminal-grid">
                <div class="terminal-cell">
                    <span>Mode</span>
                    <strong>{live_status}</strong>
                </div>
                <div class="terminal-cell">
                    <span>Source</span>
                    <strong>{source_label}</strong>
                </div>
                <div class="terminal-cell">
                    <span>Signal</span>
                    <strong class="{action_class}">{signal.action}</strong>
                </div>
                <div class="terminal-cell">
                    <span>Trend</span>
                    <strong class="{trend_class}">{trend.direction}</strong>
                </div>
                <div class="terminal-cell">
                    <span>Price Move</span>
                    <strong class="{movement.css_class}">{movement.arrow} {movement.label}</strong>
                </div>
                <div class="terminal-cell">
                    <span>Confidence</span>
                    <strong>{signal.confidence}%</strong>
                </div>
                <div class="terminal-cell">
                    <span>Last Candle</span>
                    <strong>{format_timestamp(levels.latest_time)}</strong>
                </div>
                <div class="terminal-cell">
                    <span>Refresh</span>
                    <strong>{refreshed_at}</strong>
                </div>
                <div class="terminal-cell">
                    <span>Update Pace</span>
                    <strong>{runtime.refresh_seconds}s</strong>
                </div>
                <div class="terminal-cell">
                    <span>Candles</span>
                    <strong>{candle_count}</strong>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_data_freshness(data: pd.DataFrame, request: MarketRequest, runtime: RuntimeSettings) -> None:
    freshness = build_freshness_status(data, request.interval)
    status_style = {
        "Fresh": "buy",
        "Delayed": "wait",
        "Stale": "sell",
    }.get(str(freshness["status"]), "neutral")
    source_label = "Binance / Yahoo" if "Binance" in runtime.data_source else "Yahoo Public"
    cards = [
        ("Data Status", str(freshness["status"]), str(freshness["detail"]), status_style),
        ("Last Candle", str(freshness["last_candle"]), f"{request.interval} timeframe", "neutral"),
        ("Data Age", str(freshness["age_label"]), "Perkiraan umur candle terakhir", status_style),
        ("Source", source_label, "Public market feed", "neutral"),
    ]
    html_cards = []
    for title, value, detail, style in cards:
        html_cards.append(
            (
                f'<div class="freshness-card {style}">'
                f'<span>{escape_html(title)}</span>'
                f'<strong>{escape_html(value)}</strong>'
                f'<em>{escape_html(detail)}</em>'
                f'</div>'
            )
        )

    st.markdown(
        f'<div class="freshness-grid">{"".join(html_cards)}</div>',
        unsafe_allow_html=True,
    )


def render_status_bar(
    request: MarketRequest,
    levels: MarketLevels,
    trend: TrendAnalysis,
    signal: SignalSummary,
    settings: IndicatorSettings,
    movement: PriceMovement,
) -> None:
    st.subheader(f"{request.label} Overview")

    render_signal_strip(levels, trend, signal, movement)

    trend_style = "buy" if trend.direction == "BUY" else "sell" if trend.direction == "SELL" else "wait"
    signal_style = "buy" if signal.action == "BUY" else "sell" if signal.action == "SELL" else "wait"
    rsi_style = "sell" if levels.rsi >= 70 else "buy" if levels.rsi <= 30 else "neutral"
    volatility_style = "sell" if levels.atr_percent > 5 else "wait" if levels.atr_percent > 3 else "neutral"

    overview_cards = [
        ("Harga Terakhir", format_price(levels.latest_close), "Harga market terkini", "neutral"),
        ("Perubahan", f"{movement.arrow} {format_signed(movement.change)}", f"{movement.change_percent:+.2f}% dari candle sebelumnya", movement.css_class),
        ("Bias", trend.bias, trend.strength, trend_style),
        (f"RSI {settings.rsi_window}", format_price(levels.rsi), interpret_rsi(levels.rsi), rsi_style),
        (f"ATR {settings.atr_window}", format_price(levels.atr), f"{levels.atr_percent:.2f}% volatilitas", volatility_style),
        ("AI Score", f"{signal.confidence}%", signal.action, signal_style),
        ("Support", format_price(levels.support), f"Area low dari {settings.level_window} candle", "buy"),
        ("Resistance", format_price(levels.resistance), f"Area high dari {settings.level_window} candle", "sell"),
        ("Distance to Support", format_price(levels.distance_to_support), "Jarak ke area demand", "neutral"),
        ("Distance to Resistance", format_price(levels.distance_to_resistance), "Jarak ke area supply", "neutral"),
        ("Range Periode", format_price(levels.highest_price - levels.lowest_price), "High-low aktif", "neutral"),
        ("ATR %", f"{levels.atr_percent:.2f}%", "Volatilitas relatif", volatility_style),
    ]
    render_overview_cards(overview_cards)


def render_best_setup(
    request: MarketRequest,
    levels: MarketLevels,
    trend: TrendAnalysis,
    risk_plan: RiskPlan,
    signal: SignalSummary,
    movement: PriceMovement,
) -> None:
    st.subheader("Best Setup Now")

    setup_style = "buy" if signal.action == "BUY" else "sell" if signal.action == "SELL" else "wait"
    if signal.action == "WAIT" or risk_plan.direction == "WAIT":
        setup_title = "Wait for Confirmation"
        setup_note = "Belum ada edge yang cukup kuat. Tunggu breakout, retest, liquidity sweep, atau candle rejection yang lebih jelas."
        entry_text = "No trade"
        stop_text = "-"
        target_text = "-"
        invalidation = "Setup invalid jika market tetap mixed dan confidence turun di bawah area layak trading."
    else:
        setup_title = f"{signal.action} Setup"
        setup_note = signal.summary
        entry_text = format_price(risk_plan.entry_area)
        stop_text = format_price(risk_plan.stop_loss)
        target_text = format_price(risk_plan.take_profit)
        invalidation = (
            f"Invalid jika harga menembus stop area {stop_text}, struktur berubah berlawanan, "
            "atau candle konfirmasi gagal mengikuti bias."
        )

    rr_text = f"1:{risk_plan.risk_reward:.2f}" if risk_plan.risk_reward else "-"
    html = f"""
    <div class="setup-card {setup_style}">
        <div class="setup-lead">
            <span>{escape_html(request.label)} Decision Card</span>
            <strong>{escape_html(setup_title)}</strong>
            <p>{escape_html(setup_note)}</p>
        </div>
        <div class="setup-grid">
            <div><span>Entry Zone</span><strong>{escape_html(entry_text)}</strong></div>
            <div><span>Stop Loss</span><strong>{escape_html(stop_text)}</strong></div>
            <div><span>Take Profit</span><strong>{escape_html(target_text)}</strong></div>
            <div><span>Confidence</span><strong>{signal.confidence}%</strong></div>
            <div><span>Risk:Reward</span><strong>{escape_html(rr_text)}</strong></div>
            <div><span>Last Move</span><strong class="{movement.css_class}">{escape_html(movement.arrow)} {movement.change_percent:+.2f}%</strong></div>
        </div>
        <div class="setup-footer">
            <span>Trend: {escape_html(trend.trend)} - {escape_html(trend.strength)}</span>
            <span>{escape_html(invalidation)}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_market_radar(
    request: MarketRequest,
    settings: IndicatorSettings,
    refresh_bucket: int,
) -> None:
    st.subheader("Market Radar")
    rows = []
    settings_values = (
        int(settings.ema_fast),
        int(settings.ema_slow),
        int(settings.rsi_window),
        int(settings.atr_window),
        int(settings.level_window),
        float(settings.risk_reward),
    )

    for label, symbol in PAIRS.items():
        try:
            rows.append(
                load_market_summary(
                    label,
                    symbol,
                    request.period,
                    request.interval,
                    settings_values,
                    refresh_bucket,
                )
            )
        except Exception as exc:
            rows.append(
                {
                    "Pair": label,
                    "Signal": "N/A",
                    "Confidence": 0,
                    "Trend": "N/A",
                    "Price": None,
                    "Move %": None,
                    "Freshness": "Error",
                    "Last Candle": str(exc)[:80],
                }
            )

    radar_df = pd.DataFrame(rows)
    if "Price" in radar_df:
        radar_df["Price"] = radar_df["Price"].apply(lambda value: format_price(value) if value is not None else "-")
    if "Move %" in radar_df:
        radar_df["Move %"] = radar_df["Move %"].apply(lambda value: f"{value:+.2f}%" if value is not None else "-")
    radar_df["Confidence"] = radar_df["Confidence"].apply(lambda value: f"{int(value)}%" if value is not None else "-")

    st.dataframe(
        radar_df,
        hide_index=True,
        use_container_width=True,
    )
    st.caption("Market Radar memakai timeframe dan data range yang sama dengan chart aktif. Matikan dari sidebar jika ingin load lebih ringan.")


def render_signal_strip(
    levels: MarketLevels,
    trend: TrendAnalysis,
    signal: SignalSummary,
    movement: PriceMovement,
) -> None:
    signal_class = "buy" if signal.action == "BUY" else "sell" if signal.action == "SELL" else "wait"
    trend_class = "buy" if trend.direction == "BUY" else "sell" if trend.direction == "SELL" else "wait"
    rsi_class = "sell" if levels.rsi >= 70 else "buy" if levels.rsi <= 30 else "neutral"
    volatility_class = "sell" if levels.atr_percent > 5 else "wait" if levels.atr_percent > 3 else "buy"

    st.markdown(
        f"""
        <div class="signal-strip">
          <div class="signal-pill {signal_class}">
            <span>Signal</span>
            <strong>{signal.action}</strong>
          </div>
          <div class="signal-pill {trend_class}">
            <span>Trend</span>
            <strong>{trend.direction}</strong>
          </div>
          <div class="signal-pill {movement.css_class}">
            <span>Tick</span>
            <strong>{movement.arrow} {movement.change_percent:+.2f}%</strong>
          </div>
          <div class="signal-pill {rsi_class}">
            <span>RSI</span>
            <strong>{levels.rsi:.2f}</strong>
          </div>
          <div class="signal-pill {volatility_class}">
            <span>Volatility</span>
            <strong>{levels.atr_percent:.2f}% ATR</strong>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview_cards(cards: list[tuple[str, str, str, str]]) -> None:
    html_cards = []
    for title, value, detail, style in cards:
        html_cards.append(
            (
                f'<div class="overview-card {style}">'
                f'<span>{escape_html(title)}</span>'
                f'<strong>{escape_html(value)}</strong>'
                f'<em>{escape_html(detail)}</em>'
                f'</div>'
            )
        )

    st.markdown(
        f'<div class="overview-card-grid">{"".join(html_cards)}</div>',
        unsafe_allow_html=True,
    )


def render_compact_metric_cards(cards: list[tuple[str, str, str, str]], grid_class: str) -> None:
    html_cards = []
    for title, value, detail, style in cards:
        html_cards.append(
            (
                f'<div class="compact-card {style}">'
                f'<span>{escape_html(title)}</span>'
                f'<strong>{escape_html(value)}</strong>'
                f'<em>{escape_html(detail)}</em>'
                f'</div>'
            )
        )

    st.markdown(
        f'<div class="{escape_html(grid_class)}">{"".join(html_cards)}</div>',
        unsafe_allow_html=True,
    )


def render_chart(
    data: pd.DataFrame,
    request: MarketRequest,
    levels: MarketLevels,
    settings: IndicatorSettings,
    runtime: RuntimeSettings,
) -> None:
    st.subheader(f"Pro Chart: {request.label}")

    if data.empty:
        st.warning("Chart belum bisa ditampilkan karena data kosong.")
        return

    render_plotly_chart(data, request, levels, settings, stable_view=True)
    st.caption(
        f"Zoom dan posisi chart tetap dipertahankan saat refresh {runtime.refresh_seconds} detik. "
        f"Mode aktif: {runtime.refresh_mode}."
    )


def render_lightweight_chart(
    data: pd.DataFrame,
    request: MarketRequest,
    levels: MarketLevels,
    settings: IndicatorSettings,
    runtime: RuntimeSettings,
) -> None:
    payload = build_lightweight_payload(data, settings)
    chart_id = f"tv_chart_{request.label.replace('/', '_').replace('=', '_')}_{request.interval}_{request.period}"
    storage_key = f"aiTradingDashboard.range.{request.label}.{request.period}.{request.interval}"
    follow_latest_default = True
    support = _json_number(levels.support)
    resistance = _json_number(levels.resistance)

    html = f"""
    <div class="tv-shell">
      <div class="tv-toolbar">
        <div>
          <span class="tv-symbol">{request.label}</span>
          <span class="tv-meta">{request.interval} / {request.period} / stable viewport</span>
        </div>
        <div class="tv-legend">
          <span><i class="up"></i>Bull</span>
          <span><i class="down"></i>Bear</span>
          <span><i class="ema-fast"></i>EMA {settings.ema_fast}</span>
          <span><i class="ema-slow"></i>EMA {settings.ema_slow}</span>
          <button id="{chart_id}_follow" class="tv-reset" type="button">Follow Latest</button>
          <button id="{chart_id}_reset" class="tv-reset" type="button">Reset View</button>
        </div>
      </div>
      <div id="{chart_id}_price" class="tv-chart price"></div>
      <div id="{chart_id}_rsi" class="tv-chart rsi"></div>
    </div>
    <script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
    <script>
      const payload = {json.dumps(payload)};
      const storageKey = {json.dumps(storage_key)};
      const followLatestDefault = {json.dumps(follow_latest_default)};
      const priceEl = document.getElementById("{chart_id}_price");
      const rsiEl = document.getElementById("{chart_id}_rsi");
      const resetButton = document.getElementById("{chart_id}_reset");
      const followButton = document.getElementById("{chart_id}_follow");
      const followKey = storageKey + ".follow";
      if (!window.LightweightCharts) {{
        priceEl.innerHTML = '<div class="tv-error">Chart alternatif tidak berhasil dimuat. Gunakan Pro Chart utama untuk tampilan yang lebih stabil.</div>';
        rsiEl.style.display = "none";
      }} else {{
      const common = {{
        layout: {{
          background: {{ type: "solid", color: "#08111f" }},
          textColor: "#c8d3e6",
          fontFamily: "Inter, Segoe UI, sans-serif"
        }},
        grid: {{
          vertLines: {{ color: "rgba(148, 163, 184, 0.10)" }},
          horzLines: {{ color: "rgba(148, 163, 184, 0.10)" }}
        }},
        crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
        rightPriceScale: {{ borderColor: "rgba(148, 163, 184, 0.22)" }},
        timeScale: {{
          borderColor: "rgba(148, 163, 184, 0.22)",
          timeVisible: true,
          secondsVisible: false
        }},
        localization: {{ priceFormatter: price => Number(price).toLocaleString(undefined, {{ maximumFractionDigits: 5 }}) }}
      }};

      const priceChart = LightweightCharts.createChart(priceEl, {{
        ...common,
        width: priceEl.clientWidth,
        height: 520
      }});
      const candleSeries = priceChart.addCandlestickSeries({{
        upColor: "#22c55e",
        downColor: "#ef4444",
        borderUpColor: "#22c55e",
        borderDownColor: "#ef4444",
        wickUpColor: "#22c55e",
        wickDownColor: "#ef4444"
      }});
      candleSeries.setData(payload.candles);

      const emaFast = priceChart.addLineSeries({{ color: "#38bdf8", lineWidth: 2, priceLineVisible: false }});
      emaFast.setData(payload.emaFast);
      const emaSlow = priceChart.addLineSeries({{ color: "#f59e0b", lineWidth: 2, priceLineVisible: false }});
      emaSlow.setData(payload.emaSlow);

      if (payload.volume.length > 0) {{
        const volumeSeries = priceChart.addHistogramSeries({{
          priceFormat: {{ type: "volume" }},
          priceScaleId: "",
          color: "rgba(148, 163, 184, 0.22)"
        }});
        priceChart.priceScale("").applyOptions({{ scaleMargins: {{ top: 0.82, bottom: 0 }} }});
        volumeSeries.setData(payload.volume);
      }}

      candleSeries.createPriceLine({{
        price: {support},
        color: "#22c55e",
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: "Support"
      }});
      candleSeries.createPriceLine({{
        price: {resistance},
        color: "#ef4444",
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: "Resistance"
      }});

      const rsiChart = LightweightCharts.createChart(rsiEl, {{
        ...common,
        width: rsiEl.clientWidth,
        height: 160
      }});
      const rsiSeries = rsiChart.addLineSeries({{ color: "#eab308", lineWidth: 2, priceLineVisible: false }});
      rsiSeries.setData(payload.rsi);
      rsiSeries.createPriceLine({{ price: 70, color: "#ef4444", lineStyle: LightweightCharts.LineStyle.Dotted, title: "70" }});
      rsiSeries.createPriceLine({{ price: 30, color: "#22c55e", lineStyle: LightweightCharts.LineStyle.Dotted, title: "30" }});

      let restoring = true;
      let syncing = false;
      let userInteracted = false;
      let saveTimer = null;

      function readStore(key) {{
        try {{
          const parentValue = window.parent && window.parent.localStorage ? window.parent.localStorage.getItem(key) : null;
          if (parentValue !== null) return parentValue;
        }} catch (error) {{}}
        try {{ return window.localStorage.getItem(key); }} catch (error) {{ return null; }}
      }}

      function writeStore(key, value) {{
        try {{
          if (window.parent && window.parent.localStorage) window.parent.localStorage.setItem(key, value);
        }} catch (error) {{}}
        try {{ window.localStorage.setItem(key, value); }} catch (error) {{}}
      }}

      function removeStore(key) {{
        try {{
          if (window.parent && window.parent.localStorage) window.parent.localStorage.removeItem(key);
        }} catch (error) {{}}
        try {{ window.localStorage.removeItem(key); }} catch (error) {{}}
      }}

      function setFollowState(enabled) {{
        writeStore(followKey, enabled ? "1" : "0");
        followButton.classList.toggle("active", enabled);
      }}

      function isFollowLatest() {{
        const stored = readStore(followKey);
        if (stored === null) return followLatestDefault;
        return stored === "1";
      }}

      function fitBoth() {{
        priceChart.timeScale().fitContent();
        rsiChart.timeScale().fitContent();
      }}

      function followLatest() {{
        priceChart.timeScale().scrollToRealTime();
        rsiChart.timeScale().scrollToRealTime();
      }}

      function restoreRange() {{
        try {{
          if (isFollowLatest()) {{
            followLatest();
            return;
          }}
          const stored = readStore(storageKey);
          if (!stored) {{
            fitBoth();
            return;
          }}
          const range = JSON.parse(stored);
          if (range && Number.isFinite(range.from) && Number.isFinite(range.to) && range.to > range.from) {{
            priceChart.timeScale().setVisibleLogicalRange(range);
            rsiChart.timeScale().setVisibleLogicalRange(range);
          }} else {{
            fitBoth();
          }}
        }} catch (error) {{
          fitBoth();
        }}
      }}

      function saveRange(range) {{
        if (restoring || syncing || !userInteracted || isFollowLatest()) return;
        if (!range || !Number.isFinite(range.from) || !Number.isFinite(range.to) || range.to <= range.from) return;
        window.clearTimeout(saveTimer);
        saveTimer = window.setTimeout(() => {{
          writeStore(storageKey, JSON.stringify(range));
        }}, 120);
      }}

      function markManualInteraction() {{
        userInteracted = true;
        setFollowState(false);
      }}

      ["wheel", "mousedown", "touchstart"].forEach(eventName => {{
        priceEl.addEventListener(eventName, markManualInteraction, {{ passive: true }});
        rsiEl.addEventListener(eventName, markManualInteraction, {{ passive: true }});
      }});

      priceChart.timeScale().subscribeVisibleLogicalRangeChange(range => {{
        if (syncing) return;
        syncing = true;
        if (range) {{
          rsiChart.timeScale().setVisibleLogicalRange(range);
          saveRange(range);
        }}
        window.requestAnimationFrame(() => {{ syncing = false; }});
      }});
      rsiChart.timeScale().subscribeVisibleLogicalRangeChange(range => {{
        if (syncing) return;
        syncing = true;
        if (range) {{
          priceChart.timeScale().setVisibleLogicalRange(range);
          saveRange(range);
        }}
        window.requestAnimationFrame(() => {{ syncing = false; }});
      }});

      followButton.addEventListener("click", () => {{
        userInteracted = false;
        setFollowState(true);
        followLatest();
      }});

      resetButton.addEventListener("click", () => {{
        removeStore(storageKey);
        userInteracted = false;
        setFollowState(false);
        fitBoth();
      }});

      restoreRange();
      setFollowState(isFollowLatest());
      window.setTimeout(() => {{ restoring = false; }}, 400);

      window.addEventListener("resize", () => {{
        priceChart.applyOptions({{ width: priceEl.clientWidth }});
        rsiChart.applyOptions({{ width: rsiEl.clientWidth }});
      }});
      }}
    </script>
    <style>
      .tv-shell {{
        background: #08111f;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 10px;
        overflow: hidden;
        font-family: Inter, Segoe UI, sans-serif;
      }}
      .tv-toolbar {{
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 14px;
        background: #0c1628;
        border-bottom: 1px solid rgba(148, 163, 184, 0.16);
      }}
      .tv-symbol {{
        color: #f8fafc;
        font-weight: 750;
        margin-right: 10px;
      }}
      .tv-meta, .tv-legend {{
        color: #94a3b8;
        font-size: 12px;
      }}
      .tv-legend {{
        display: flex;
        gap: 12px;
        align-items: center;
        flex-wrap: wrap;
      }}
      .tv-legend i {{
        display: inline-block;
        width: 10px;
        height: 3px;
        margin-right: 5px;
        vertical-align: middle;
      }}
      .tv-legend .up {{ background: #22c55e; }}
      .tv-legend .down {{ background: #ef4444; }}
      .tv-legend .ema-fast {{ background: #38bdf8; }}
      .tv-legend .ema-slow {{ background: #f59e0b; }}
      .tv-chart {{ width: 100%; }}
      .tv-chart.rsi {{ border-top: 1px solid rgba(148, 163, 184, 0.14); }}
      .tv-error {{
        min-height: 520px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        color: #fbbf24;
        text-align: center;
        font-size: 14px;
      }}
      .tv-reset {{
        border: 1px solid rgba(148, 163, 184, 0.26);
        border-radius: 7px;
        background: rgba(15, 23, 42, 0.92);
        color: #dbeafe;
        font-size: 12px;
        padding: 6px 10px;
        cursor: pointer;
        transition: border-color 160ms ease, color 160ms ease, background 160ms ease, transform 160ms ease;
      }}
      .tv-reset:hover {{ border-color: rgba(56, 189, 248, 0.72); color: #f8fafc; }}
      .tv-reset.active {{
        border-color: rgba(34, 197, 94, 0.58);
        background: rgba(34, 197, 94, 0.14);
        color: #dcfce7;
      }}
    </style>
    """
    components.html(html, height=760, scrolling=False)


def render_plotly_chart(
    data: pd.DataFrame,
    request: MarketRequest,
    levels: MarketLevels,
    settings: IndicatorSettings,
    stable_view: bool,
) -> None:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.72, 0.28],
    )
    fig.add_trace(
        go.Candlestick(
            x=data["Timestamp"],
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Candlestick",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=data["Timestamp"],
            y=data["EMA_FAST"],
            mode="lines",
            name=f"EMA {settings.ema_fast}",
            line=dict(width=1.8),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=data["Timestamp"],
            y=data["EMA_SLOW"],
            mode="lines",
            name=f"EMA {settings.ema_slow}",
            line=dict(width=1.8),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=data["Timestamp"],
            y=data["RSI"],
            mode="lines",
            name=f"RSI {settings.rsi_window}",
            line=dict(width=1.5, color="#f1c40f"),
        ),
        row=2,
        col=1,
    )

    fig.add_hline(
        y=levels.support,
        line_dash="dash",
        line_color="#2ecc71",
        annotation_text="Support",
        annotation_position="bottom right",
        row=1,
        col=1,
    )
    fig.add_hline(
        y=levels.resistance,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text="Resistance",
        annotation_position="top right",
        row=1,
        col=1,
    )
    fig.add_hline(y=70, line_dash="dot", line_color="#e74c3c", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#2ecc71", row=2, col=1)

    fig.update_layout(
        height=700,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        title=f"{request.label} Technical Chart",
        dragmode="pan",
        transition=dict(duration=220, easing="cubic-in-out"),
        uirevision=(
            f"{request.label}-{request.period}-{request.interval}-{settings.ema_fast}-{settings.ema_slow}"
            if stable_view
            else None
        ),
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"pro_chart_{request.label}_{request.period}_{request.interval}_{settings.ema_fast}_{settings.ema_slow}",
        config={
            "displayModeBar": False,
            "scrollZoom": True,
            "responsive": True,
        },
    )


def render_analysis(
    levels: MarketLevels,
    trend: TrendAnalysis,
    signal: SignalSummary,
    movement: PriceMovement,
) -> None:
    st.subheader("Market Analysis")

    bias_col, score_col = st.columns(2, gap="medium")
    with bias_col:
        st.markdown('<div class="panel-title">Market Reading</div>', unsafe_allow_html=True)
        analysis_points = build_market_analysis_points(levels, trend, signal, movement)
        render_info_cards(analysis_points)

    with score_col:
        st.markdown('<div class="panel-title">Signal Factors</div>', unsafe_allow_html=True)
        render_signal_factor_cards(signal)


def render_risk_plan(risk_plan: RiskPlan) -> None:
    st.subheader("Risk Plan")

    if risk_plan.direction == "WAIT":
        st.info(risk_plan.note)
        return

    render_risk_cards(risk_plan)
    st.caption(risk_plan.note)


def render_decision_lab(
    data: pd.DataFrame,
    request: MarketRequest,
    settings: IndicatorSettings,
    runtime: RuntimeSettings,
    signal_history: list[dict[str, object]],
) -> None:
    st.subheader("Decision Lab")
    columns = []
    if runtime.show_backtest:
        columns.append("backtest")
    if runtime.show_signal_history:
        columns.append("history")
    if not columns:
        return

    if len(columns) == 2:
        backtest_col, history_col = st.columns(2, gap="medium")
        with backtest_col:
            render_backtest_snapshot(data, settings)
        with history_col:
            render_signal_history(signal_history)
        return

    if columns[0] == "backtest":
        render_backtest_snapshot(data, settings)
    else:
        render_signal_history(signal_history)


def render_backtest_snapshot(data: pd.DataFrame, settings: IndicatorSettings) -> None:
    result = calculate_backtest_snapshot(data, settings)
    st.markdown('<div class="panel-title">Backtest Snapshot</div>', unsafe_allow_html=True)
    cards = [
        ("Trades", str(result["trades"]), "Valid setup pada data aktif", "neutral"),
        ("Win Rate", f'{result["win_rate"]:.1f}%', "TP lebih dulu tersentuh", "buy" if result["win_rate"] >= 50 else "wait"),
        ("Avg R", f'{result["avg_r"]:+.2f}R', "Rata-rata hasil per setup", "buy" if result["avg_r"] > 0 else "sell"),
        ("Open / Timeout", str(result["open_trades"]), "Setup belum selesai dalam horizon", "neutral"),
    ]
    render_compact_metric_cards(cards, "lab-card-grid")
    st.caption(
        "Backtest ini snapshot rule-based dari data yang sedang tampil. Gunakan sebagai validasi awal, bukan jaminan performa live."
    )


def render_signal_history(history: list[dict[str, object]]) -> None:
    st.markdown('<div class="panel-title">Session Signal History</div>', unsafe_allow_html=True)
    if not history:
        st.info("Riwayat sinyal akan muncul setelah dashboard membaca candle pertama pada sesi ini.")
        return

    history_df = pd.DataFrame(history[:12]).drop(columns=["_key"], errors="ignore")
    st.dataframe(history_df, hide_index=True, use_container_width=True)
    st.caption("Riwayat ini tersimpan di sesi browser saat ini. Untuk versi berbayar, ini bisa dipindah ke database permanen.")


def render_detail_panels(
    data: pd.DataFrame,
    levels: MarketLevels,
    trend: TrendAnalysis,
    risk_plan: RiskPlan,
    signal: SignalSummary,
    settings: IndicatorSettings,
    movement: PriceMovement,
) -> None:
    st.subheader("Detailed Trading Information")

    technical_tab, candle_tab, structure_tab, ict_tab, risk_tab, signal_tab, integrity_tab = st.tabs(
        ["Technical", "Price Action", "Market Structure", "ICT Framework", "Risk", "Signal Model", "Data Integrity"]
    )

    with technical_tab:
        ema_spread = levels.ema_fast - levels.ema_slow
        rows = [
            ("EMA Fast", format_price(levels.ema_fast), f"EMA {settings.ema_fast}"),
            ("EMA Slow", format_price(levels.ema_slow), f"EMA {settings.ema_slow}"),
            ("EMA Spread", format_price(ema_spread), interpret_ema_spread(ema_spread, levels.latest_close)),
            ("RSI", format_price(levels.rsi), interpret_rsi(levels.rsi)),
            ("ATR", format_price(levels.atr), interpret_volatility(levels.atr_percent)),
            ("Support", format_price(levels.support), f"Lowest low dari {settings.level_window} candle terakhir"),
            ("Resistance", format_price(levels.resistance), f"Highest high dari {settings.level_window} candle terakhir"),
        ]
        st.dataframe(
            pd.DataFrame(rows, columns=["Metric", "Value", "Interpretation"]),
            hide_index=True,
            use_container_width=True,
        )

    with candle_tab:
        candle = build_candle_profile(data)
        candle["Tick Movement"] = f"{movement.arrow} {movement.label}"
        candle["Tick Change"] = f"{format_signed(movement.change)} ({movement.change_percent:+.2f}%)"
        st.dataframe(
            pd.DataFrame(candle.items(), columns=["Candle Detail", "Value"]),
            hide_index=True,
            use_container_width=True,
        )

    with structure_tab:
        rows = build_market_structure_rows(levels, trend, movement)
        st.dataframe(
            pd.DataFrame(rows, columns=["Structure", "Value", "Reading"]),
            hide_index=True,
            use_container_width=True,
        )

    with ict_tab:
        ict_rows = build_ict_framework_rows(data, levels, trend)
        st.dataframe(
            pd.DataFrame(ict_rows, columns=["ICT Concept", "Reading", "How To Use"]),
            hide_index=True,
            use_container_width=True,
        )

    with risk_tab:
        rows = [
            ("Direction", risk_plan.direction),
            ("Entry Area", format_price(risk_plan.entry_area)),
            ("Stop Loss", format_price(risk_plan.stop_loss)),
            ("Take Profit", format_price(risk_plan.take_profit)),
            ("Risk", format_price(risk_plan.risk)),
            ("Reward", format_price(risk_plan.reward)),
            ("Risk Reward", f"1:{risk_plan.risk_reward:.2f}" if risk_plan.risk_reward else "-"),
            ("Plan Note", risk_plan.note),
        ]
        st.dataframe(
            pd.DataFrame(rows, columns=["Risk Component", "Value"]),
            hide_index=True,
            use_container_width=True,
        )

    with signal_tab:
        factor_rows = [
            (factor.name, factor.score, factor.detail)
            for factor in signal.factors
        ]
        st.dataframe(
            pd.DataFrame(factor_rows, columns=["Factor", "Score", "Reason"]),
            hide_index=True,
            use_container_width=True,
        )
        st.write(f"**Final Action:** {signal.action}")
        st.write(f"**Confidence:** {signal.confidence}%")
        st.write(f"**Model Note:** {signal.summary}")
        st.write(f"**Trend Note:** {trend.explanation}")

    with integrity_tab:
        integrity_rows = build_data_integrity_rows(data)
        st.dataframe(
            pd.DataFrame(integrity_rows, columns=["Check", "Status", "Detail"]),
            hide_index=True,
            use_container_width=True,
        )


def render_context(request: MarketRequest) -> None:
    st.subheader("Market Context")
    context_items = build_market_context(request.label, request.period, request.interval)
    cards = [(item.title, item.detail, "neutral") for item in context_items]
    cards.extend(
        [
            (
                "Data Policy",
                "BTC/ETH memakai data publik Binance sebagai prioritas; market lain memakai data publik Yahoo. Feed broker bisa ditambahkan untuk versi produksi.",
                "wait",
            ),
            (
                "Client Readiness",
                "Sinyal dirangkum dari trend, momentum, area harga, volatilitas, dan risk plan sehingga mudah diaudit sebelum dipakai klien.",
                "buy",
            ),
        ]
    )
    render_info_cards(cards)


def render_disclaimer() -> None:
    st.info(
        "Dashboard ini memakai data publik dan berfungsi sebagai decision-support, bukan sinyal eksekusi otomatis. "
        "Selalu validasi harga, spread, berita besar, dan manajemen risiko melalui broker sebelum mengambil posisi."
    )


def render_footer() -> None:
    current_year = 2026
    st.markdown(
        f"""
        <footer class="app-footer">
            <div>
                <strong>AI Trading Dashboard&trade;</strong>
                <span>&copy; {current_year} Muhammad Alfazry Ramadhani. All rights reserved.</span>
            </div>
            <p>
                Trademark notice: AI Trading Dashboard&trade; merupakan identitas produk dan karya digital
                Muhammad Alfazry Ramadhani. Penggunaan ulang, distribusi, atau komersialisasi tanpa izin
                tertulis tidak diperbolehkan.
            </p>
        </footer>
        """,
        unsafe_allow_html=True,
    )


def build_lightweight_payload(data: pd.DataFrame, settings: IndicatorSettings) -> dict[str, list[dict[str, float | int | str]]]:
    chart_data = data.tail(1500).copy()
    candles: list[dict[str, float | int | str]] = []
    ema_fast: list[dict[str, float | int | str]] = []
    ema_slow: list[dict[str, float | int | str]] = []
    rsi: list[dict[str, float | int | str]] = []
    volume: list[dict[str, float | int | str]] = []

    for row in chart_data.itertuples(index=False):
        row_data = row._asdict()
        timestamp = timestamp_to_chart_time(row_data["Timestamp"])
        open_price = _float_or_none(row_data["Open"])
        high_price = _float_or_none(row_data["High"])
        low_price = _float_or_none(row_data["Low"])
        close_price = _float_or_none(row_data["Close"])
        if None in (open_price, high_price, low_price, close_price):
            continue

        candles.append(
            {
                "time": timestamp,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
            }
        )
        add_line_point(ema_fast, timestamp, row_data.get("EMA_FAST"))
        add_line_point(ema_slow, timestamp, row_data.get("EMA_SLOW"))
        add_line_point(rsi, timestamp, row_data.get("RSI"))

        volume_value = _float_or_none(row_data.get("Volume"))
        if volume_value and volume_value > 0:
            color = "rgba(34, 197, 94, 0.28)" if close_price >= open_price else "rgba(239, 68, 68, 0.28)"
            volume.append({"time": timestamp, "value": volume_value, "color": color})

    del settings
    return {
        "candles": candles,
        "emaFast": ema_fast,
        "emaSlow": ema_slow,
        "rsi": rsi,
        "volume": volume,
    }


def add_line_point(target: list[dict[str, float | int | str]], timestamp: int, value: object) -> None:
    number = _float_or_none(value)
    if number is not None:
        target.append({"time": timestamp, "value": number})


def build_candle_profile(data: pd.DataFrame) -> dict[str, str]:
    last = data.iloc[-1]
    open_price = float(last["Open"])
    high_price = float(last["High"])
    low_price = float(last["Low"])
    close_price = float(last["Close"])
    candle_range = max(high_price - low_price, 0.0)
    body = abs(close_price - open_price)
    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price
    direction = "Bullish" if close_price > open_price else "Bearish" if close_price < open_price else "Doji"

    return {
        "Time": format_timestamp(last["Timestamp"]),
        "Direction": direction,
        "Open": format_price(open_price),
        "High": format_price(high_price),
        "Low": format_price(low_price),
        "Close": format_price(close_price),
        "Body": format_price(body),
        "Range": format_price(candle_range),
        "Body % of Range": f"{(body / candle_range * 100):.2f}%" if candle_range else "-",
        "Upper Wick": format_price(upper_wick),
        "Lower Wick": format_price(lower_wick),
    }


def calculate_price_movement(data: pd.DataFrame) -> PriceMovement:
    if len(data) < 2:
        return PriceMovement(
            direction="flat",
            arrow="-",
            css_class="neutral",
            change=0.0,
            change_percent=0.0,
            label="No change",
        )

    latest = float(data["Close"].iloc[-1])
    previous = float(data["Close"].iloc[-2])
    change = latest - previous
    change_percent = (change / previous * 100) if previous else 0.0

    if change > 0:
        return PriceMovement(
            direction="up",
            arrow="▲",
            css_class="buy",
            change=change,
            change_percent=change_percent,
            label="Up",
        )
    if change < 0:
        return PriceMovement(
            direction="down",
            arrow="▼",
            css_class="sell",
            change=change,
            change_percent=change_percent,
            label="Down",
        )
    return PriceMovement(
        direction="flat",
        arrow="-",
        css_class="neutral",
        change=0.0,
        change_percent=0.0,
        label="Flat",
    )


def build_freshness_status(data: pd.DataFrame, interval: str) -> dict[str, object]:
    if data.empty or "Timestamp" not in data.columns:
        return {
            "status": "Unknown",
            "detail": "Timestamp belum tersedia",
            "last_candle": "-",
            "age_label": "-",
            "age_seconds": None,
        }

    latest_timestamp = pd.to_datetime(data["Timestamp"].iloc[-1], utc=True, errors="coerce")
    if pd.isna(latest_timestamp):
        return {
            "status": "Unknown",
            "detail": "Timestamp tidak bisa dibaca",
            "last_candle": format_timestamp(data["Timestamp"].iloc[-1]),
            "age_label": "-",
            "age_seconds": None,
        }

    age_seconds = max((pd.Timestamp.now(tz="UTC") - latest_timestamp).total_seconds(), 0.0)
    interval_seconds = interval_to_seconds(interval)
    fresh_limit = max(interval_seconds * 2.5, 900)
    stale_limit = max(interval_seconds * 8, 3_600)
    if interval == "1d":
        fresh_limit = 172_800
        stale_limit = 432_000

    if age_seconds <= fresh_limit:
        status = "Fresh"
        detail = "Data masih relevan untuk monitoring aktif"
    elif age_seconds <= stale_limit:
        status = "Delayed"
        detail = "Masih dapat dianalisis, tetapi perlu validasi broker"
    else:
        status = "Stale"
        detail = "Cek ulang source sebelum mengambil keputusan"

    return {
        "status": status,
        "detail": detail,
        "last_candle": format_timestamp(latest_timestamp),
        "age_label": format_duration(age_seconds),
        "age_seconds": age_seconds,
    }


def interval_to_seconds(interval: str) -> int:
    try:
        amount = int(interval[:-1])
    except ValueError:
        return 3_600
    unit = interval[-1]
    if unit == "m":
        return amount * 60
    if unit == "h":
        return amount * 3_600
    if unit == "d":
        return amount * 86_400
    return 3_600


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    seconds = max(float(seconds), 0.0)
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3_600:
        return f"{int(seconds // 60)}m"
    if seconds < 86_400:
        hours = int(seconds // 3_600)
        minutes = int((seconds % 3_600) // 60)
        return f"{hours}h {minutes}m"
    days = int(seconds // 86_400)
    hours = int((seconds % 86_400) // 3_600)
    return f"{days}d {hours}h"


def update_signal_history(
    request: MarketRequest,
    levels: MarketLevels,
    trend: TrendAnalysis,
    risk_plan: RiskPlan,
    signal: SignalSummary,
    movement: PriceMovement,
) -> list[dict[str, object]]:
    if "signal_history" not in st.session_state:
        st.session_state["signal_history"] = []

    key = "|".join(
        [
            request.label,
            request.interval,
            str(format_timestamp(levels.latest_time)),
            signal.action,
            str(signal.confidence),
        ]
    )
    history = list(st.session_state["signal_history"])
    if history and history[0].get("_key") == key:
        return history

    row = {
        "_key": key,
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Pair": request.label,
        "TF": request.interval,
        "Signal": signal.action,
        "Confidence": f"{signal.confidence}%",
        "Trend": trend.direction,
        "Move": f"{movement.change_percent:+.2f}%",
        "Entry": format_price(risk_plan.entry_area),
        "SL": format_price(risk_plan.stop_loss),
        "TP": format_price(risk_plan.take_profit),
    }
    history.insert(0, row)
    st.session_state["signal_history"] = history[:100]
    return st.session_state["signal_history"]


def calculate_backtest_snapshot(data: pd.DataFrame, settings: IndicatorSettings) -> dict[str, float | int]:
    data = data.tail(700).reset_index(drop=True)
    if len(data) < max(settings.ema_slow, settings.level_window, settings.rsi_window, settings.atr_window) + 12:
        return {"trades": 0, "wins": 0, "losses": 0, "open_trades": 0, "win_rate": 0.0, "avg_r": 0.0}

    start_index = max(settings.ema_slow, settings.level_window, settings.rsi_window, settings.atr_window) + 2
    horizon = 8 if settings.level_window <= 60 else 5
    trades = 0
    wins = 0
    losses = 0
    open_trades = 0
    r_values: list[float] = []

    for index in range(start_index, len(data) - horizon):
        sample = data.iloc[: index + 1]
        try:
            levels = calculate_levels(sample, settings)
            trend = analyze_trend(levels)
            risk_plan = calculate_risk_plan(levels, trend, settings)
            signal = build_signal_summary(levels, trend, risk_plan)
        except Exception:
            continue

        if signal.action == "WAIT" or signal.confidence < 60 or risk_plan.risk is None or risk_plan.risk <= 0:
            continue

        entry = float(sample["Close"].iloc[-1])
        atr = max(float(levels.atr), 0.0)
        if atr <= 0:
            continue

        if signal.action == "BUY":
            stop_loss = entry - atr
            take_profit = entry + (atr * settings.risk_reward)
        else:
            stop_loss = entry + atr
            take_profit = entry - (atr * settings.risk_reward)

        future = data.iloc[index + 1 : index + 1 + horizon]
        outcome = evaluate_trade_outcome(signal.action, entry, stop_loss, take_profit, future)
        trades += 1
        if outcome == "win":
            wins += 1
            r_values.append(float(settings.risk_reward))
        elif outcome == "loss":
            losses += 1
            r_values.append(-1.0)
        else:
            open_trades += 1
            last_close = float(future["Close"].iloc[-1]) if not future.empty else entry
            open_r = (last_close - entry) / atr if signal.action == "BUY" else (entry - last_close) / atr
            r_values.append(max(min(open_r, float(settings.risk_reward)), -1.0))

    resolved = wins + losses
    win_rate = (wins / resolved * 100) if resolved else 0.0
    avg_r = (sum(r_values) / len(r_values)) if r_values else 0.0
    return {
        "trades": trades,
        "wins": wins,
        "losses": losses,
        "open_trades": open_trades,
        "win_rate": win_rate,
        "avg_r": avg_r,
    }


def evaluate_trade_outcome(
    direction: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    future: pd.DataFrame,
) -> str:
    for row in future.itertuples(index=False):
        row_data = row._asdict()
        high = float(row_data["High"])
        low = float(row_data["Low"])
        if direction == "BUY":
            hit_stop = low <= stop_loss
            hit_target = high >= take_profit
        else:
            hit_stop = high >= stop_loss
            hit_target = low <= take_profit

        if hit_stop and hit_target:
            return "loss"
        if hit_target:
            return "win"
        if hit_stop:
            return "loss"
    return "open"


def build_market_analysis_points(
    levels: MarketLevels,
    trend: TrendAnalysis,
    signal: SignalSummary,
    movement: PriceMovement,
) -> list[tuple[str, str, str]]:
    range_size = max(levels.resistance - levels.support, 0.0)
    support_ratio = levels.distance_to_support / range_size if range_size else 0.0
    resistance_ratio = levels.distance_to_resistance / range_size if range_size else 0.0

    if signal.action == "BUY":
        action_style = "buy"
        action_note = "Prioritas buy hanya jika harga memberi pullback/rejection yang jelas."
        summary_style = "buy"
    elif signal.action == "SELL":
        action_style = "sell"
        action_note = "Prioritas sell hanya jika harga memberi pullback/rejection yang jelas."
        summary_style = "sell"
    else:
        action_style = "wait"
        action_note = "Tidak ada keunggulan kuat; tunggu breakout, retest, atau candle konfirmasi."
        summary_style = "wait"

    location_note = "Harga berada di tengah range."
    location_style = "neutral"
    if support_ratio <= 0.25:
        location_note = "Harga dekat support; pantau reaksi buyer atau breakdown."
        location_style = "buy"
    elif resistance_ratio <= 0.25:
        location_note = "Harga dekat resistance; pantau rejection seller atau breakout."
        location_style = "sell"

    return [
        ("Action Bias", f"{signal.action} - {signal.confidence}%", action_style),
        ("Signal Summary", signal.summary, summary_style),
        ("Trend Reading", f"{trend.trend} - {trend.strength}", action_style if trend.direction == signal.action else "neutral"),
        ("Tick Direction", f"{movement.arrow} {movement.label} ({movement.change_percent:+.2f}%)", movement.css_class),
        ("Price Location", location_note, location_style),
        ("RSI Context", interpret_rsi(levels.rsi), "sell" if levels.rsi >= 70 else "buy" if levels.rsi <= 30 else "neutral"),
        ("Volatility", interpret_volatility(levels.atr_percent), "sell" if levels.atr_percent > 5 else "wait" if levels.atr_percent > 3 else "buy"),
        ("Execution Note", action_note, action_style),
    ]


def build_market_structure_rows(
    levels: MarketLevels,
    trend: TrendAnalysis,
    movement: PriceMovement,
) -> list[tuple[str, str, str]]:
    range_size = max(levels.resistance - levels.support, 0.0)
    range_position = ((levels.latest_close - levels.support) / range_size * 100) if range_size else 0.0
    ema_spread = levels.ema_fast - levels.ema_slow

    return [
        ("Current Price", format_price(levels.latest_close), f"{movement.arrow} {movement.label} from previous candle"),
        ("Trend State", trend.trend, trend.explanation),
        ("Range Position", f"{range_position:.2f}%", "0% dekat support, 100% dekat resistance."),
        ("Support Distance", format_price(levels.distance_to_support), "Ruang turun menuju support terdekat."),
        ("Resistance Distance", format_price(levels.distance_to_resistance), "Ruang naik menuju resistance terdekat."),
        ("EMA Spread", format_price(ema_spread), interpret_ema_spread(ema_spread, levels.latest_close)),
        ("Volatility Regime", f"{levels.atr_percent:.2f}% ATR", interpret_volatility(levels.atr_percent)),
    ]


def build_ict_framework_rows(
    data: pd.DataFrame,
    levels: MarketLevels,
    trend: TrendAnalysis,
) -> list[tuple[str, str, str]]:
    range_size = max(levels.resistance - levels.support, 0.0)
    equilibrium = levels.support + (range_size * 0.5) if range_size else levels.latest_close
    range_position = ((levels.latest_close - levels.support) / range_size * 100) if range_size else 50.0

    if levels.latest_close > equilibrium:
        premium_discount = f"Premium zone ({range_position:.1f}%)"
        pd_note = "Lebih selektif untuk buy; pantau sell-side rejection atau FVG retest."
    else:
        premium_discount = f"Discount zone ({range_position:.1f}%)"
        pd_note = "Lebih selektif untuk sell; pantau buy-side rejection atau FVG retest."

    sweep_reading = detect_liquidity_sweep(data)
    fvg_reading = detect_simple_fvg(data)
    bias_note = "Bullish delivery model" if trend.direction == "BUY" else "Bearish delivery model" if trend.direction == "SELL" else "No clear delivery model"

    return [
        ("Premium / Discount", premium_discount, pd_note),
        ("Liquidity Sweep", sweep_reading, "Cari konfirmasi displacement setelah sweep, bukan entry buta."),
        ("Fair Value Gap", fvg_reading, "Gunakan sebagai area retest jika searah dengan bias dan struktur."),
        ("Delivery Bias", bias_note, "Gabungkan dengan BOS/CHoCH sebelum membuat keputusan entry."),
        ("Model Status", "Foundation mode", "Framework ICT ini masih advisory; perlu backtest sebelum dipakai sebagai sinyal utama."),
    ]


def detect_liquidity_sweep(data: pd.DataFrame) -> str:
    if len(data) < 12:
        return "Insufficient candles"

    recent = data.tail(12)
    last = recent.iloc[-1]
    previous = recent.iloc[:-1]
    previous_high = float(previous["High"].max())
    previous_low = float(previous["Low"].min())
    last_high = float(last["High"])
    last_low = float(last["Low"])
    last_close = float(last["Close"])

    if last_high > previous_high and last_close < previous_high:
        return "Buy-side liquidity sweep candidate"
    if last_low < previous_low and last_close > previous_low:
        return "Sell-side liquidity sweep candidate"
    return "No fresh sweep detected"


def detect_simple_fvg(data: pd.DataFrame) -> str:
    if len(data) < 3:
        return "Insufficient candles"

    c1 = data.iloc[-3]
    c3 = data.iloc[-1]
    c1_high = float(c1["High"])
    c1_low = float(c1["Low"])
    c3_high = float(c3["High"])
    c3_low = float(c3["Low"])

    if c3_low > c1_high:
        return f"Bullish FVG candidate: {format_price(c1_high)} - {format_price(c3_low)}"
    if c3_high < c1_low:
        return f"Bearish FVG candidate: {format_price(c3_high)} - {format_price(c1_low)}"
    return "No active 3-candle FVG"


def build_data_integrity_rows(data: pd.DataFrame) -> list[tuple[str, str, str]]:
    required_columns = ["Timestamp", "Open", "High", "Low", "Close"]
    missing_columns = [column for column in required_columns if column not in data.columns]
    duplicate_timestamps = int(data["Timestamp"].duplicated().sum()) if "Timestamp" in data.columns else 0
    missing_price_values = int(data[[column for column in required_columns if column in data.columns]].isna().sum().sum())
    candle_count = len(data)
    latest_time = format_timestamp(data["Timestamp"].iloc[-1]) if "Timestamp" in data.columns and not data.empty else "-"
    has_volume = "Volume" in data.columns and data["Volume"].notna().any()
    monotonic_time = bool(data["Timestamp"].is_monotonic_increasing) if "Timestamp" in data.columns and not data.empty else False
    invalid_ohlc = 0
    if not missing_columns and not data.empty:
        invalid_ohlc = int(
            (
                (data["High"] < data[["Open", "Close", "Low"]].max(axis=1))
                | (data["Low"] > data[["Open", "Close", "High"]].min(axis=1))
            ).sum()
        )

    rows = [
        ("Required Columns", "OK" if not missing_columns else "Warning", "Lengkap" if not missing_columns else ", ".join(missing_columns)),
        ("Candle Count", "OK" if candle_count >= 30 else "Warning", f"{candle_count} candles loaded"),
        ("Latest Timestamp", "OK" if latest_time != "-" else "Warning", latest_time),
        ("Time Order", "OK" if monotonic_time else "Warning", "Timestamp berurutan" if monotonic_time else "Timestamp perlu dicek"),
        ("Duplicate Timestamp", "OK" if duplicate_timestamps == 0 else "Warning", f"{duplicate_timestamps} duplicate rows"),
        ("Missing OHLC Values", "OK" if missing_price_values == 0 else "Warning", f"{missing_price_values} missing values"),
        ("OHLC Consistency", "OK" if invalid_ohlc == 0 else "Warning", f"{invalid_ohlc} candle tidak konsisten"),
        ("Volume Data", "OK" if has_volume else "Info", "Available" if has_volume else "Tidak tersedia dari source untuk kombinasi ini"),
        ("Update Integrity", "Info", "Data diperbarui berkala dari source publik; gunakan harga broker untuk keputusan eksekusi."),
    ]
    return rows


def render_info_cards(cards: list[tuple[str, str, str]]) -> None:
    html_cards = []
    for title, value, style in cards:
        html_cards.append(
            f'<div class="info-card {style}"><span>{escape_html(title)}</span><strong>{escape_html(value)}</strong></div>'
        )

    st.markdown(
        f"<div class='info-card-grid'>{''.join(html_cards)}</div>",
        unsafe_allow_html=True,
    )


def render_signal_factor_cards(signal: SignalSummary) -> None:
    html_cards = []
    for factor in signal.factors:
        percent = min(max(factor.score / 30 * 100, 0), 100)
        style = factor_style(factor.name, factor.score)
        html_cards.append(
            f'<div class="factor-card {style}"><div class="factor-top"><span>{escape_html(factor.name)}</span><strong>{factor.score} pts</strong></div><div class="factor-bar"><i style="width:{percent:.1f}%"></i></div><p>{escape_html(factor.detail)}</p></div>'
        )

    st.markdown(
        f'<div class="factor-summary"><span>Total Confidence</span><strong>{signal.confidence}%</strong><em>{escape_html(signal.label)} - {signal.action}</em></div><div class="factor-grid">{"".join(html_cards)}</div>',
        unsafe_allow_html=True,
    )


def render_risk_cards(risk_plan: RiskPlan) -> None:
    direction_style = "buy" if risk_plan.direction == "BUY" else "sell" if risk_plan.direction == "SELL" else "wait"
    risk_reward = f"1:{risk_plan.risk_reward:.2f}" if risk_plan.risk_reward else "-"
    cards = [
        ("Entry", f"{risk_plan.direction} {format_price(risk_plan.entry_area)}", direction_style),
        ("Stop Loss", format_price(risk_plan.stop_loss), "sell"),
        ("Take Profit", format_price(risk_plan.take_profit), "buy"),
        ("Risk", format_price(risk_plan.risk), "sell"),
        ("Reward", format_price(risk_plan.reward), "buy"),
        ("R:R", risk_reward, direction_style),
    ]
    html_cards = []
    for title, value, style in cards:
        html_cards.append(
            f'<div class="risk-card {style}"><span>{escape_html(title)}</span><strong>{escape_html(value)}</strong></div>'
        )

    st.markdown(
        f"<div class='risk-card-grid'>{''.join(html_cards)}</div>",
        unsafe_allow_html=True,
    )


def factor_style(name: str, score: int) -> str:
    if score >= 20:
        return "buy"
    if score <= 8:
        return "sell"
    if name.lower() in {"volatilitas", "risk plan"} and score <= 10:
        return "wait"
    return "neutral"


def format_signed(value: float | None) -> str:
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return f"{sign}{format_price(value)}"


def escape_html(value: object) -> str:
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def interpret_rsi(rsi: float) -> str:
    if rsi >= 70:
        return "Overbought, tunggu pullback atau konfirmasi breakout."
    if rsi <= 30:
        return "Oversold, waspada rebound."
    if rsi >= 55:
        return "Momentum bullish moderat."
    if rsi <= 45:
        return "Momentum bearish moderat."
    return "Netral."


def interpret_volatility(atr_percent: float) -> str:
    if atr_percent <= 0:
        return "ATR belum valid."
    if atr_percent <= 1.5:
        return "Volatilitas rendah."
    if atr_percent <= 3.5:
        return "Volatilitas normal."
    if atr_percent <= 6:
        return "Volatilitas tinggi, kecilkan lot."
    return "Volatilitas ekstrem, risiko whipsaw tinggi."


def interpret_ema_spread(ema_spread: float, latest_close: float) -> str:
    spread_percent = abs(ema_spread) / latest_close * 100 if latest_close else 0
    direction = "fast EMA di atas slow EMA" if ema_spread > 0 else "fast EMA di bawah slow EMA"
    if spread_percent >= 1:
        return f"{direction}, trend mulai jelas ({spread_percent:.2f}%)."
    return f"{direction}, tetapi jarak EMA masih tipis ({spread_percent:.2f}%)."


def timestamp_to_chart_time(value: object) -> int:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    return int(timestamp.timestamp())


def format_timestamp(value: object) -> str:
    try:
        timestamp = pd.Timestamp(value)
        return timestamp.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)


def _float_or_none(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return round(number, 8)


def _json_number(value: float) -> str:
    return json.dumps(round(float(value), 8))


def render_global_styles() -> None:
    st.markdown(
        """
        <style>
          :root {
            --bg: #07111f;
            --panel: #0b1424;
            --panel-2: #101b2f;
            --border: rgba(148, 163, 184, 0.16);
            --text: #e5edf8;
            --muted: #91a0b7;
            --buy: #22c55e;
            --sell: #ef4444;
            --wait: #f59e0b;
            --blue: #38bdf8;
          }
          .stApp {
            background:
              radial-gradient(circle at top left, rgba(20, 184, 166, 0.10), transparent 30%),
              linear-gradient(180deg, #07111f 0%, #0a1020 100%);
            color: var(--text);
            font-family: Inter, "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
          }
          html, body, [class*="css"] {
            font-family: Inter, "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
            letter-spacing: 0;
          }
          h1, h2, h3 {
            letter-spacing: 0;
            font-weight: 750;
          }
          p, label, span, div {
            letter-spacing: 0;
          }
          [data-testid="stSidebar"] {
            background: #08111f;
            border-right: 1px solid rgba(148, 163, 184, 0.16);
          }
          [data-testid="stSidebar"] .block-container,
          [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.2rem;
          }
          [data-testid="stSidebar"] label,
          [data-testid="stSidebar"] p,
          [data-testid="stSidebar"] span {
            color: #cbd5e1;
          }
          .sidebar-panel {
            padding: 14px 14px 13px;
            margin: 0 0 14px 0;
            border-radius: 12px;
            border: 1px solid rgba(56, 189, 248, 0.18);
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.10), rgba(15, 23, 42, 0.80));
          }
          .sidebar-panel.compact {
            margin-top: 18px;
          }
          .sidebar-panel span {
            display: block;
            color: #f8fafc !important;
            font-size: 13px;
            font-weight: 820;
            text-transform: uppercase;
            margin-bottom: 6px;
          }
          .sidebar-panel p {
            margin: 0;
            color: #94a3b8 !important;
            font-size: 12px;
            line-height: 1.45;
          }
          .sidebar-note {
            margin: 10px 0 4px;
            padding: 11px 12px;
            border-radius: 10px;
            border: 1px solid rgba(34, 197, 94, 0.20);
            background: rgba(34, 197, 94, 0.08);
            color: #b7c6d9;
            font-size: 12px;
            line-height: 1.45;
          }
          [data-testid="stSidebar"] div[data-baseweb="select"] > div,
          [data-testid="stSidebar"] div[data-baseweb="input"] > div,
          [data-testid="stSidebar"] [role="radiogroup"] {
            border-radius: 10px;
          }
          [data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 10px;
            padding: 14px 16px;
            transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
          }
          [data-testid="stMetric"]:hover {
            transform: translateY(-1px);
            border-color: rgba(56, 189, 248, 0.32);
            background: rgba(15, 23, 42, 0.88);
          }
          [data-testid="stMetric"] label {
            color: #94a3b8;
            font-size: 12px;
            font-weight: 650;
          }
          [data-testid="stMetricValue"] {
            color: #f8fafc;
            font-variant-numeric: tabular-nums;
            font-weight: 760;
          }
          [data-testid="stMetricDelta"] {
            font-variant-numeric: tabular-nums;
          }
          .terminal-header {
            display: block;
            padding: 22px;
            margin-bottom: 18px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 12px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(8, 17, 31, 0.94));
            box-shadow: 0 22px 70px rgba(0, 0, 0, 0.24);
          }
          .terminal-header h1 {
            margin: 4px 0 8px 0;
            font-size: 34px;
            letter-spacing: 0;
            color: #f8fafc;
          }
          .terminal-header p {
            margin: 0;
            color: #94a3b8;
            max-width: 680px;
          }
          .eyebrow {
            color: #38bdf8;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0;
          }
          .terminal-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 12px;
            width: 100%;
            margin-top: 18px;
          }
          .terminal-cell {
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 10px;
            padding: 13px 14px;
            background: rgba(2, 6, 23, 0.42);
            min-height: 88px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
          }
          .terminal-cell:hover {
            transform: translateY(-1px);
            border-color: rgba(56, 189, 248, 0.30);
            background: rgba(8, 17, 31, 0.76);
          }
          .terminal-cell span {
            display: block;
            color: #94a3b8;
            font-size: 12px;
            margin-bottom: 8px;
            font-weight: 720;
            text-transform: uppercase;
          }
          .terminal-cell strong {
            color: #f8fafc;
            font-size: clamp(15px, 1.05vw, 18px);
            font-weight: 820;
            font-variant-numeric: tabular-nums;
            overflow-wrap: anywhere;
          }
          .terminal-cell strong.buy { color: #22c55e; }
          .terminal-cell strong.sell { color: #ef4444; }
          .terminal-cell strong.wait { color: #f59e0b; }
          .terminal-cell strong.neutral { color: #cbd5e1; }
          .signal-strip {
            display: grid;
            grid-template-columns: repeat(5, minmax(120px, 1fr));
            gap: 10px;
            margin: 4px 0 14px 0;
          }
          .signal-pill {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 10px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(15, 23, 42, 0.78);
            transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
          }
          .signal-pill:hover {
            transform: translateY(-1px);
            border-color: rgba(56, 189, 248, 0.34);
          }
          .signal-pill span {
            color: #94a3b8;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
          }
          .signal-pill strong {
            font-size: 15px;
            font-weight: 800;
            font-variant-numeric: tabular-nums;
          }
          .signal-pill.buy {
            border-color: rgba(34, 197, 94, 0.34);
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.14), rgba(15, 23, 42, 0.82));
          }
          .signal-pill.sell {
            border-color: rgba(239, 68, 68, 0.34);
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.14), rgba(15, 23, 42, 0.82));
          }
          .signal-pill.wait {
            border-color: rgba(245, 158, 11, 0.34);
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.14), rgba(15, 23, 42, 0.82));
          }
          .signal-pill.neutral {
            border-color: rgba(148, 163, 184, 0.22);
          }
          .signal-pill.buy strong { color: #22c55e; }
          .signal-pill.sell strong { color: #ef4444; }
          .signal-pill.wait strong { color: #f59e0b; }
          .signal-pill.neutral strong { color: #cbd5e1; }
          .freshness-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: -4px 0 18px;
          }
          .freshness-card,
          .compact-card {
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 12px;
            padding: 13px 14px;
            background: rgba(15, 23, 42, 0.70);
            min-height: 92px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
          }
          .freshness-card:hover,
          .compact-card:hover {
            transform: translateY(-1px);
            border-color: rgba(56, 189, 248, 0.30);
            background: rgba(15, 23, 42, 0.86);
          }
          .freshness-card span,
          .compact-card span {
            color: #9fb2cc;
            font-size: 11px;
            font-weight: 780;
            text-transform: uppercase;
          }
          .freshness-card strong,
          .compact-card strong {
            color: #f8fafc;
            font-size: 20px;
            font-weight: 850;
            font-variant-numeric: tabular-nums;
            overflow-wrap: anywhere;
          }
          .freshness-card em,
          .compact-card em {
            color: #8ea0b8;
            font-size: 11px;
            font-style: normal;
            line-height: 1.35;
          }
          .freshness-card.buy,
          .compact-card.buy {
            border-color: rgba(34, 197, 94, 0.28);
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.10), rgba(15, 23, 42, 0.76));
          }
          .freshness-card.sell,
          .compact-card.sell {
            border-color: rgba(239, 68, 68, 0.28);
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.10), rgba(15, 23, 42, 0.76));
          }
          .freshness-card.wait,
          .compact-card.wait {
            border-color: rgba(245, 158, 11, 0.28);
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.10), rgba(15, 23, 42, 0.76));
          }
          .overview-card-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 12px;
            margin: 12px 0 18px;
          }
          .overview-card {
            min-height: 116px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 12px;
            padding: 15px 16px;
            background: rgba(15, 23, 42, 0.72);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
          }
          .overview-card:hover {
            transform: translateY(-1px);
            border-color: rgba(56, 189, 248, 0.32);
            background: rgba(15, 23, 42, 0.88);
          }
          .overview-card span {
            color: #9cc4ee;
            font-size: 12px;
            font-weight: 720;
            line-height: 1.25;
          }
          .overview-card strong {
            color: #f8fafc;
            font-size: clamp(23px, 1.7vw, 33px);
            font-weight: 850;
            line-height: 1.05;
            font-variant-numeric: tabular-nums;
            overflow-wrap: anywhere;
          }
          .overview-card em {
            min-height: 30px;
            color: #91a0b7;
            font-style: normal;
            font-size: 11px;
            line-height: 1.35;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
          }
          .overview-card.buy {
            border-color: rgba(34, 197, 94, 0.28);
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.10), rgba(15, 23, 42, 0.76));
          }
          .overview-card.sell {
            border-color: rgba(239, 68, 68, 0.28);
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.10), rgba(15, 23, 42, 0.76));
          }
          .overview-card.wait {
            border-color: rgba(245, 158, 11, 0.28);
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.10), rgba(15, 23, 42, 0.76));
          }
          .overview-card.neutral {
            border-color: rgba(148, 163, 184, 0.16);
          }
          .overview-card.buy strong { color: #22c55e; }
          .overview-card.sell strong { color: #ef4444; }
          .overview-card.wait strong { color: #f59e0b; }
          .setup-card {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 14px;
            padding: 18px;
            margin: 4px 0 18px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(8, 17, 31, 0.92));
            box-shadow: 0 20px 55px rgba(0, 0, 0, 0.18);
          }
          .setup-card.buy { border-color: rgba(34, 197, 94, 0.28); }
          .setup-card.sell { border-color: rgba(239, 68, 68, 0.28); }
          .setup-card.wait { border-color: rgba(245, 158, 11, 0.28); }
          .setup-lead {
            margin-bottom: 16px;
          }
          .setup-lead span {
            display: block;
            color: #38bdf8;
            font-size: 12px;
            font-weight: 820;
            text-transform: uppercase;
            margin-bottom: 5px;
          }
          .setup-lead strong {
            display: block;
            color: #f8fafc;
            font-size: 26px;
            font-weight: 880;
            line-height: 1.1;
          }
          .setup-lead p {
            margin: 8px 0 0;
            color: #aab7ca;
            max-width: 900px;
          }
          .setup-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 10px;
          }
          .setup-grid div {
            min-height: 82px;
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 10px;
            padding: 12px;
            background: rgba(2, 6, 23, 0.30);
            display: flex;
            flex-direction: column;
            justify-content: center;
          }
          .setup-grid span {
            color: #94a3b8;
            font-size: 11px;
            font-weight: 760;
            text-transform: uppercase;
            margin-bottom: 8px;
          }
          .setup-grid strong {
            color: #f8fafc;
            font-size: 18px;
            font-weight: 840;
            font-variant-numeric: tabular-nums;
            overflow-wrap: anywhere;
          }
          .setup-grid strong.buy { color: #22c55e; }
          .setup-grid strong.sell { color: #ef4444; }
          .setup-footer {
            display: grid;
            grid-template-columns: 0.7fr 1.3fr;
            gap: 10px;
            margin-top: 12px;
          }
          .setup-footer span {
            border-radius: 10px;
            padding: 10px 12px;
            background: rgba(15, 23, 42, 0.62);
            border: 1px solid rgba(148, 163, 184, 0.12);
            color: #b6c4d8;
            font-size: 12px;
            line-height: 1.4;
          }
          .lab-card-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-bottom: 10px;
          }
          .panel-title {
            color: #f8fafc;
            font-size: 15px;
            font-weight: 820;
            margin: 2px 0 12px;
          }
          div[data-testid="stPlotlyChart"] {
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 12px;
            overflow: hidden;
            background: rgba(2, 6, 23, 0.30);
          }
          .info-card-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(220px, 1fr));
            gap: 10px;
            margin-bottom: 14px;
            align-items: stretch;
          }
          .info-card {
            min-height: 112px;
            padding: 13px 14px;
            border-radius: 10px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(15, 23, 42, 0.72);
            animation: panelIn 220ms ease both;
            transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
          }
          .info-card:hover {
            transform: translateY(-1px);
            border-color: rgba(56, 189, 248, 0.28);
          }
          .info-card span {
            display: block;
            color: #94a3b8;
            font-size: 11px;
            font-weight: 780;
            text-transform: uppercase;
            margin-bottom: 8px;
          }
          .info-card strong {
            display: block;
            color: #e5edf8;
            font-size: 14px;
            font-weight: 650;
            line-height: 1.35;
          }
          .info-card.buy {
            border-color: rgba(34, 197, 94, 0.30);
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.10), rgba(15, 23, 42, 0.74));
          }
          .info-card.sell {
            border-color: rgba(239, 68, 68, 0.30);
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.10), rgba(15, 23, 42, 0.74));
          }
          .info-card.wait {
            border-color: rgba(245, 158, 11, 0.30);
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.10), rgba(15, 23, 42, 0.74));
          }
          .info-card.neutral {
            border-color: rgba(148, 163, 184, 0.16);
          }
          .factor-summary {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 2px 12px;
            align-items: end;
            padding: 14px;
            margin-bottom: 10px;
            min-height: 90px;
            border: 1px solid rgba(56, 189, 248, 0.22);
            border-radius: 12px;
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.11), rgba(15, 23, 42, 0.82));
            animation: panelIn 220ms ease both;
          }
          .factor-summary span {
            color: #94a3b8;
            font-size: 12px;
            font-weight: 760;
            text-transform: uppercase;
          }
          .factor-summary strong {
            color: #f8fafc;
            font-size: 26px;
            font-weight: 860;
            font-variant-numeric: tabular-nums;
            line-height: 1;
          }
          .factor-summary em {
            grid-column: 1 / -1;
            color: #cbd5e1;
            font-style: normal;
            font-size: 13px;
          }
          .factor-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
          }
          .factor-card {
            min-height: 112px;
            padding: 12px;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(15, 23, 42, 0.72);
            animation: panelIn 220ms ease both;
            transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
          }
          .factor-card:hover {
            transform: translateY(-1px);
            border-color: rgba(56, 189, 248, 0.32);
          }
          .factor-top {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
            margin-bottom: 9px;
          }
          .factor-top span {
            color: #dbeafe;
            font-size: 13px;
            font-weight: 780;
          }
          .factor-top strong {
            color: #f8fafc;
            font-size: 13px;
            font-weight: 820;
            font-variant-numeric: tabular-nums;
          }
          .factor-bar {
            height: 9px;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(30, 41, 59, 0.92);
            margin-bottom: 9px;
          }
          .factor-bar i {
            display: block;
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #38bdf8, #22c55e);
            transition: width 320ms ease;
          }
          .factor-card.sell .factor-bar i { background: linear-gradient(90deg, #f97316, #ef4444); }
          .factor-card.wait .factor-bar i { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
          .factor-card.neutral .factor-bar i { background: linear-gradient(90deg, #64748b, #38bdf8); }
          .factor-card p {
            margin: 0;
            color: #aab7ca;
            font-size: 12px;
            line-height: 1.35;
          }
          .risk-card-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 8px;
          }
          .risk-card {
            min-height: 94px;
            padding: 14px;
            border-radius: 13px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(15, 23, 42, 0.76);
            animation: panelIn 220ms ease both;
            transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
          }
          .risk-card:hover {
            transform: translateY(-1px);
            border-color: rgba(56, 189, 248, 0.32);
          }
          .risk-card span {
            display: block;
            color: #94a3b8;
            font-size: 11px;
            font-weight: 780;
            text-transform: uppercase;
            margin-bottom: 10px;
          }
          .risk-card strong {
            color: #f8fafc;
            font-size: 19px;
            font-weight: 840;
            font-variant-numeric: tabular-nums;
            line-height: 1.1;
          }
          .risk-card.buy {
            border-color: rgba(34, 197, 94, 0.30);
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.12), rgba(15, 23, 42, 0.78));
          }
          .risk-card.sell {
            border-color: rgba(239, 68, 68, 0.30);
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(15, 23, 42, 0.78));
          }
          .risk-card.wait {
            border-color: rgba(245, 158, 11, 0.30);
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(15, 23, 42, 0.78));
          }
          div[data-testid="stDataFrame"] {
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 10px;
            overflow: hidden;
          }
          .app-footer {
            margin: 28px 0 6px;
            padding: 18px 20px;
            border-top: 1px solid rgba(148, 163, 184, 0.14);
            color: #7f8da3;
            text-align: center;
          }
          .app-footer div {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 6px;
          }
          .app-footer strong {
            color: #c8d5e8;
            font-size: 13px;
            font-weight: 820;
          }
          .app-footer span,
          .app-footer p {
            color: #7f8da3;
            font-size: 12px;
            line-height: 1.5;
          }
          .app-footer p {
            max-width: 860px;
            margin: 0 auto;
          }
          .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
          }
          .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            background: rgba(15, 23, 42, 0.62);
            border: 1px solid rgba(148, 163, 184, 0.12);
            color: #cbd5e1;
            font-weight: 700;
            padding: 8px 12px;
          }
          .stTabs [aria-selected="true"] {
            border-color: rgba(56, 189, 248, 0.42);
            color: #f8fafc;
          }
          .stTabs [data-baseweb="tab-panel"] {
            animation: panelIn 220ms ease both;
          }
          @keyframes panelIn {
            from {
              opacity: 0;
              transform: translateY(6px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          @media (max-width: 1200px) {
            .overview-card-grid {
              grid-template-columns: repeat(3, minmax(0, 1fr));
            }
            .setup-grid {
              grid-template-columns: repeat(3, minmax(0, 1fr));
            }
          }
          @media (max-width: 900px) {
            .terminal-grid {
              min-width: 0;
              grid-template-columns: repeat(2, minmax(120px, 1fr));
            }
            .freshness-grid {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .signal-strip {
              grid-template-columns: repeat(2, minmax(120px, 1fr));
            }
            .overview-card-grid {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .setup-grid,
            .setup-footer,
            .lab-card-grid {
              grid-template-columns: 1fr;
            }
            .info-card-grid {
              grid-template-columns: 1fr;
            }
            .factor-grid {
              grid-template-columns: 1fr;
            }
            .risk-card-grid {
              grid-template-columns: repeat(2, minmax(120px, 1fr));
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
