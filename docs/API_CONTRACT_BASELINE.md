# API Contract Baseline

Dokumen ini mencatat kontrak FastAPI saat ini sebagai baseline sebelum migrasi lebih jauh.

## 1) Ringkasan Endpoint

Base app: `apps/api/main.py`

Endpoint aktif:
1. `GET /`
2. `GET /health`
3. `GET /symbols`
4. `POST /analyze`
5. `POST /cockpit/analyze`

## 2) Detail Endpoint

## `GET /`
- Tujuan: root status cepat.
- Response:
```json
{
  "status": "ok",
  "service": "trading-dashboard-api",
  "docs": "/docs"
}
```

## `GET /health`
- Tujuan: health check service.
- Response:
```json
{
  "status": "ok",
  "service": "trading-dashboard-api"
}
```

## `GET /symbols`
- Tujuan: daftar simbol/timeframe yang didukung.
- Data source: `services.market_data_service.get_supported_symbols/get_supported_timeframes`
- Response:
```json
{
  "symbols": ["XAUUSD", "BTCUSD", "..."],
  "timeframes": ["M15", "M30", "H1", "H4", "D1"]
}
```

## `POST /analyze`
- File route: `apps/api/routes/analysis.py`
- Request body (Pydantic `AnalyzeRequestBody`):
```json
{
  "symbol": "BTCUSD",
  "timeframe": "H1"
}
```
- Success response: serialisasi `schemas.dto.AnalysisResult` (via `dataclasses.asdict`).
- Field utama response:
  - top-level: `symbol`, `timeframe`, `bias`, `signal`, `confidence`, `risk_level`, `trade_quality_score`, `reasons`, `warnings`
  - nested:
    - `technical_summary`
    - `sentiment_summary`
    - `risk_summary`
    - `market_regime`
  - lite fields:
    - `market_context_lite`
    - `risk_gate_lite`
    - `data_health_lite`
    - `signal_explanation_lite`
    - `signal_contribution_lite`
- Error behavior:
  - `400` untuk input invalid (ValueError)
  - `503` untuk service unavailable

## `POST /cockpit/analyze`
- File route: `apps/api/routes/cockpit.py`
- Request body (Pydantic `CockpitAnalyzeRequestBody`):
```json
{
  "symbol": "BTCUSD",
  "timeframe": "H1"
}
```
- Success response: serialisasi `schemas.cockpit.CockpitAnalysisResult`.
- Field utama response:
  - metadata: `schema_version`, `symbol`, `timeframe`
  - section contract:
    - `price_snapshot`
    - `market_overview`
    - `market_context`
    - `signal_decision`
    - `confidence_breakdown`
    - `evidence_layer`
    - `multi_timeframe`
    - `regime_analysis`
    - `market_structure`
    - `risk_plan`
    - `risk_gate`
    - `data_quality`
    - `sentiment_context`
    - `backtest_snapshot`
    - `validation_notes`
    - `ui_sections`
    - `feature_flags`
    - `legacy_result` (AnalysisResult)
- Error behavior:
  - `400` untuk input invalid
  - `503` untuk service unavailable

## 3) Schema Utama yang Dipakai

## Legacy Schema
- File: `schemas/dto.py`
- Root: `AnalysisResult`
- Nested:
  - `TechnicalSummary`
  - `SentimentSummary`
  - `RiskResult`
  - `MarketRegimeResult`

## Cockpit Schema
- File: `schemas/cockpit.py`
- Root: `CockpitAnalysisResult`
- Semua section membawa `status` (`available`, `partial`, `caution`, `not_available`) untuk fallback UI.

## 4) Kecocokan untuk Next.js (Parity Phase)

Status saat ini: **cukup siap untuk dipakai Next.js sebagai mirror**, dengan catatan:

Kelebihan:
1. Kontrak sudah terstruktur dan stabil untuk dua mode (legacy + cockpit).
2. Ada fallback semantics melalui `status` per section.
3. Request body sederhana (`symbol`, `timeframe`) dan cocok untuk query UI.
4. Sudah ada test kontrak/integrasi API.

Keterbatasan yang perlu diperhatikan:
1. Belum ada versioning endpoint formal (contoh `/v1/...`), walau ada `schema_version` di cockpit payload.
2. Belum ada auth layer/caller identity untuk konsumsi multi-frontend production.
3. Belum ada pagination/filter untuk histori karena endpoint fokus real-time analysis.
4. Response cukup besar untuk `cockpit/analyze`; Next.js perlu selective rendering/caching.

## 5) Rekomendasi Kontrak Sebelum Frontend Mirror Penuh

1. Pertahankan field existing (jangan breaking change).
2. Jika tambah field baru, buat optional dan additive.
3. Pertimbangkan namespace versioning route (`/v1`) saat mulai expose publik.
4. Tambahkan metadata observability ringan (request id, generated_at) secara non-breaking.

