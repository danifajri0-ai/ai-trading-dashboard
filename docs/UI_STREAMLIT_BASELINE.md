# UI Streamlit Baseline

Dokumen ini mengunci baseline UI Streamlit aktif sebelum migrasi ke Supabase, Render, dan Vercel.

Prinsip:
- Streamlit tetap aktif.
- Tidak ada redesign besar di fase audit/migrasi awal.
- UI baru (Next.js) nanti harus meniru baseline ini dulu (parity), baru enhancement.

## 1) Ringkasan Struktur UI Saat Ini

- Entrypoint: `apps/streamlit_app/app.py`
- Selector + kontrol tampilan: `apps/streamlit_app/ui/sidebar.py`
- Render mode:
  - Rich Cockpit v2 (default): `apps/streamlit_app/ui/cockpit_renderer.py` + `apps/streamlit_app/ui/components/*`
  - Legacy dashboard (fallback): `signal_card.py`, `chart_panel.py`, `risk_panel.py`, `market_table.py`, `warning_panel.py`
- API client mode `http_api`: `apps/streamlit_app/client/api_client.py`

## 2) Section UI yang Ada Sekarang

## A. Layout Utama
- Sidebar kiri + area dashboard utama.
- Cockpit v2 flow:
  1. Command Header
  2. Decision Map + post-chart summary
  3. Grid utama: market state, signal decision, risk execution
  4. Deep Analysis Console (tab Evidence/Timeframes/Regime/Data/Performance/Sentiment/Radar)
- Legacy flow tetap ada sebagai fallback render.

## B. Pair/Timeframe Selector (Wajib Dipertahankan)
- Lokasi: `ui/sidebar.py`
- Komponen:
  - `selectbox("Symbol", ...)`
  - `selectbox("Timeframe", ...)`
  - toggle radar/decision lab
  - density mode + refresh interval
- Data source:
  - `GET /symbols` saat `SETTINGS.mode == "http_api"`
  - fallback `services.market_data_service.get_supported_symbols/get_supported_timeframes`

## C. Command Header / Hero Ringkas
- Cockpit v2: `ui/components/trading_desk_header.py`
- Menampilkan:
  - Symbol/timeframe
  - Price snapshot
  - Signal/Bias/Confidence/Validation/Data quality/Risk gate
  - Source status (api/local/fallback)
- Data source:
  - `CockpitAnalysisResult.price_snapshot`
  - `market_overview`
  - `signal_decision`
  - `data_quality`
  - `risk_gate`

## D. Market Overview / Market State
- Cockpit v2: `ui/components/market_overview_panel.py`
- Legacy: `ui/signal_card.py` bagian "Market Overview"
- Menampilkan:
  - Trend pressure, momentum, volatility, execution quality, data health
  - Summary market
- Data source:
  - `market_overview`
  - `signal_decision`
  - `regime_analysis`
  - `data_quality`
  - `risk_gate`
  - fallback legacy: `AnalysisResult.technical_summary`, `market_regime`

## E. Signal / Bias / Confidence (Wajib Dipertahankan)
- Cockpit v2:
  - status chips di header
  - detail di `ui/components/signal_decision_panel.py`
- Legacy:
  - "Signal Decision" di `ui/signal_card.py`
- Menampilkan:
  - Action/signal, bias, confidence
  - valid/blocked/selective/ready state
  - confirmation/warning/blocker
- Data source:
  - `market_overview.signal/bias/confidence`
  - `signal_decision.*`
  - fallback: `AnalysisResult.signal/bias/confidence`

## F. Indicator & Chart Panel (Wajib Dipertahankan)
- Legacy chart utama: `ui/chart_panel.py`
  - Candlestick, EMA20/EMA50, RSI, volume, support/resistance
- Cockpit decision map: `ui/components/chart_zone_panel.py`
  - entry/stop/target mapping + setup checklist
- Heatmap kontribusi: `ui/components/heatmap_panel.py`
- Data source:
  - Legacy: `AnalysisResult.technical_summary`, `risk_summary`, `market_regime`, `market_frame`
  - Cockpit: `price_snapshot`, `market_overview`, `risk_plan`, `risk_gate`, `market_structure`, `confidence_breakdown`

## G. Sentiment Panel (Wajib Dipertahankan)
- Cockpit v2: `ui/components/sentiment_panel.py`
- Legacy: tab "News Context" di `ui/market_table.py`
- Menampilkan:
  - sentiment label/score/source
  - context & caveat/notes
- Data source:
  - `sentiment_context.*`
  - fallback: `AnalysisResult.sentiment_summary.*`

## H. Risk Plan (Wajib Dipertahankan)
- Cockpit v2: `ui/components/risk_panel.py`
- Legacy: `ui/risk_panel.py`
- Menampilkan:
  - Entry/SL/TP, risk-reward, max risk, risk level
  - risk gate status & reasons
  - (legacy) session signal history
- Data source:
  - `risk_plan.*`
  - `risk_gate.*`
  - fallback: `AnalysisResult.risk_summary`, `risk_gate_lite`
  - session-only: `st.session_state["signal_history"]`, `risk_gate_history`

## I. Market Context (Wajib Dipertahankan)
- Legacy explicit section: `ui/signal_card.py` ("Market Context")
- Cockpit implicit context via:
  - `market_overview_panel.py`
  - `regime_panel.py`
  - `data_quality_panel.py`
- Data source:
  - `market_context.context`
  - `regime_analysis.*`
  - `data_quality.*`
  - fallback: `market_context_lite`, `market_regime`

## J. Setup Strategy / Decision Lab (Wajib Dipertahankan)
- Cockpit:
  - `signal_decision_panel.py`
  - `decision_lab_panel.py`
  - checklist di `chart_zone_panel.py`
- Legacy:
  - setup title BUY/SELL/WAIT di `signal_card.py`
  - "Decision Lab" snapshot di `risk_panel.py`
- Data source:
  - `signal_decision.*`
  - `risk_plan.*`
  - `risk_gate.*`
  - `market_overview.trade_quality_score`

## K. Market Detail & Tabel Audit
- Legacy tab multi-seksi: `ui/market_table.py`
  - Technical Analysis, Price Action, ICT Strategy, Market Structure, Risk, Signal Model, News Context, Data Integrity
  - Market Radar + mini heatmap
- Data source:
  - `AnalysisResult` + `market_frame` + `radar_rows`
  - radar_rows dibangun dari `_build_market_radar()` di `app.py`

## 3) Komponen/Panel yang Wajib Dipertahankan

Minimal set yang wajib ada selama migrasi:
1. Pair/timeframe selector di sidebar.
2. Market overview state panel.
3. Signal/bias/confidence panel.
4. Indicator/chart panel.
5. Sentiment panel.
6. Risk plan panel.
7. Market context panel.
8. Setup strategy/decision panel.
9. Market radar atau ekuivalen ringkas lintas pair.

## 4) Data Source Mapping (Ringkas)

- Sumber utama analisis legacy:
  - `services.analysis_service.analyze_market()` -> `schemas.dto.AnalysisResult`
- Sumber utama cockpit:
  - `services.cockpit_service.analyze_cockpit_market()` -> `schemas.cockpit.CockpitAnalysisResult`
- Jalur API:
  - `POST /analyze` -> payload `AnalysisResult`
  - `POST /cockpit/analyze` -> payload `CockpitAnalysisResult`
- Jalur local fallback:
  - saat API tidak tersedia, Streamlit fallback ke local service.

## 5) Catatan Redundan / Double (Jangan Dihapus Dulu)

Temuan redundansi yang sengaja dipertahankan dulu untuk safety:
1. Terdapat dua gaya render:
   - Cockpit v2 dan legacy dashboard sama-sama aktif/fallback.
2. Informasi Signal/Bias/Confidence muncul di beberapa tempat:
   - header, signal panel, decision lab.
3. Risk summary tampil di panel risk dan di beberapa summary card chart zone.
4. Sentiment/context tampil di panel dedicated dan di sebagian rationale legacy.
5. Utility komponen legacy ada duplikasi:
   - `apps/streamlit_app/ui/components.py`
   - `apps/streamlit_app/ui/components/__init__.py`

Catatan: redundansi ini bukan bug fatal, tetapi perlu dibersihkan bertahap setelah parity Next.js tercapai dan baseline kontrak stabil.

## 6) Baseline Lock untuk Migrasi

Selama fase migrasi awal:
- Jangan hilangkan panel wajib.
- Jangan ubah label/signifikansi field inti tanpa update kontrak dan dokumentasi.
- Gunakan status fallback (`available/caution/not_available`) untuk ketahanan UI saat data parsial.

