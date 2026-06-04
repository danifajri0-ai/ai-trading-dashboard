# AI Trading Dashboard

Trading dashboard dengan arsitektur layer bertahap:
- Streamlit frontend (`apps/streamlit_app`)
- FastAPI backend paralel (`apps/api`)
- Service + domain terpisah untuk analisa

Dokumen ini fokus pada cara kerja arsitektur terbaru dan developer workflow.

## Rujukan Inti

- [API Contract Baseline](</C:/Users/Diel2011/Documents/Project LLM/ai_trading_dashboard_prototipe/docs/API_CONTRACT_BASELINE.md>)
- [Supabase Setup](</C:/Users/Diel2011/Documents/Project LLM/ai_trading_dashboard_prototipe/docs/SUPABASE_SETUP.md>)
- [UI Streamlit Baseline](</C:/Users/Diel2011/Documents/Project LLM/ai_trading_dashboard_prototipe/docs/UI_STREAMLIT_BASELINE.md>)

## Struktur Folder Terbaru

```text
ai_trading_dashboard_prototipe/
├── apps/
│   ├── streamlit_app/
│   │   ├── app.py
│   │   ├── client/
│   │   └── ui/
│   └── api/
│       ├── main.py
│       ├── routes/
│       └── client_test.py
├── domain/
├── services/
├── infrastructure/
│   └── providers/
├── schemas/
├── config/
├── tests/
├── scripts/
├── runtime/                      # artefak lokal: cache market, signal history, sqlite
├── app.py                        # entrypoint lama (tetap tersedia)
├── market_data.py                # wrapper/backward compatibility
├── technical_analysis.py         # wrapper/backward compatibility
├── ai_signal.py                  # wrapper/backward compatibility
├── sentiment_news.py             # wrapper/backward compatibility
├── requirements.txt
└── run_dashboard.bat
```

## Penjelasan Layer

- `apps/streamlit_app`
  - Frontend Streamlit.
  - UI hanya merender `AnalysisResult`.
  - Mode bisa `local_service` atau `http_api`.

- `apps/api`
  - Adapter HTTP (FastAPI).
  - Tidak memanggil domain langsung.
  - Endpoint:
    - `GET /health`
    - `GET /symbols`
    - `POST /analyze`

- `domain`
  - Pure analysis logic (indikator, signal engine, risk engine, market regime, sentiment engine).
  - Tidak import Streamlit.
  - Tidak mengambil data market langsung.

- `services`
  - Facade use-case.
  - `market_data_service.py`: akses data market terstandar.
  - `analysis_service.py`: satu pintu analisa `analyze_market(symbol, timeframe)`.

- `infrastructure`
  - Integrasi provider eksternal / data source.
  - `providers/market_data_provider.py`
  - `providers/news_provider.py`
  - `providers/cache_provider.py`

- `schemas`
  - Kontrak DTO, terutama `AnalysisResult` dkk.

- `config`
  - Konfigurasi aplikasi (`settings.py`), termasuk mode:
    - `local_service`
    - `http_api`

- `tests`
  - Unit test service/domain/schema + boundary checks.

## Setup Cepat

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-local.txt
pip install -r requirements-api-local.txt
pip install -r requirements-market-local.txt
```

## Menjalankan Streamlit (local_service mode)

Opsi 1 (direkomendasikan):

```text
scripts\run_streamlit.bat
```

Opsi 2 manual:

```powershell
venv\Scripts\python.exe -m streamlit run apps/streamlit_app/app.py
```

Mode default saat ini ada di `config/settings.py`:

```python
mode: AppMode = "local_service"
```

## Menjalankan FastAPI

Opsi 1 (direkomendasikan):

```text
scripts\run_api.bat
```

Opsi 2 manual:

```powershell
venv\Scripts\python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs:
- http://127.0.0.1:8000/docs

## Deploy Vercel

- Source of truth Vercel saat ini adalah project root `ai_trading_dashboard_prototipe` yang membaca [vercel.json](</C:/Users/Diel2011/Documents/Project LLM/ai_trading_dashboard_prototipe/vercel.json>) dengan `experimentalServices` untuk:
  - `apps/web` pada route `/`
  - `apps/api/vercel_entry.py` pada route `/backend`
- Jika ada project Vercel lain bernama `web`, anggap itu legacy/terpisah dan bukan target deploy utama repo ini.
- Env production untuk persistence backend harus dipasang di project root `ai_trading_dashboard_prototipe`, bukan di project `web` terpisah.
- Jika env root belum ada, frontend tetap bisa hidup tetapi endpoint history/watchlist akan fallback karena backend persistence berjalan dalam mode disabled.
- Halaman `/settings` menampilkan status env frontend opsional, tetapi itu bukan source of truth untuk persistence backend.

Env minimum untuk root production:

```env
SUPABASE_ENABLED=true
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_ANON_KEY=<anon-key-optional>
```

Catatan:
- `SUPABASE_SERVICE_ROLE_KEY` hanya untuk backend. Jangan expose key ini ke browser atau variabel `NEXT_PUBLIC_*`.
- `NEXT_PUBLIC_SUPABASE_URL` dan `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` hanya relevan kalau nanti frontend browser/session Supabase benar-benar dipakai.
- Untuk bootstrap schema production, jalankan juga migration `supabase/migrations/0004_revoke_anon_mutable_table_privileges.sql` agar `anon` tetap read-only pada tabel mutable.
- Jika butuh data publik non-Binance secara lokal, install juga `requirements-market-local.txt`.

Audit lokal deploy bisa dijalankan dengan:

```powershell
venv\Scripts\python.exe scripts\check_deploy_ready.py
```

## Mengganti Mode ke `http_api`

Edit file [config/settings.py](</C:/Users/Diel2011/Documents/Project LLM/ai_trading_dashboard_prototipe/config/settings.py>):

```python
mode: AppMode = "http_api"
```

Alur saat `http_api`:
1. Streamlit memanggil API client (`apps/streamlit_app/client/api_client.py`).
2. Jika backend gagal, UI menampilkan error jelas.
3. Dashboard fallback otomatis ke `local_service`.

## Menjalankan Pytest

Cara menjalankan test:

```text
scripts\run_tests.bat
```

Opsi 1:

```text
scripts\run_tests.bat
```

Opsi 2 manual:

```powershell
venv\Scripts\python.exe -m pytest -q
```

## Cara Menambah Symbol Baru

1. Tambahkan simbol di [config/settings.py](</C:/Users/Diel2011/Documents/Project LLM/ai_trading_dashboard_prototipe/config/settings.py>) pada `supported_symbols`.
2. Tambahkan mapping simbol ke provider symbol di:
   - [services/market_data_service.py](</C:/Users/Diel2011/Documents/Project LLM/ai_trading_dashboard_prototipe/services/market_data_service.py>)
   - bagian `provider_symbol_map`.
3. (Opsional) Tambahkan konteks aset di:
   - [domain/sentiment_engine.py](</C:/Users/Diel2011/Documents/Project LLM/ai_trading_dashboard_prototipe/domain/sentiment_engine.py>)
4. Jalankan test:
   - `scripts\run_tests.bat`

## Cara Menambah Provider Market Data Baru

1. Buat provider baru di `infrastructure/providers/` (contoh: `new_feed_provider.py`).
2. Pastikan provider hanya mengembalikan data mentah/awal (tanpa hitung signal).
3. Integrasikan provider di:
   - [infrastructure/providers/market_data_provider.py](</C:/Users/Diel2011/Documents/Project LLM/ai_trading_dashboard_prototipe/infrastructure/providers/market_data_provider.py>)
   - sebagai primary/fallback source.
4. Pastikan output akhirnya tetap format konsisten:
   - `Timestamp, Open, High, Low, Close, Volume`
5. Validasi dengan:
   - `scripts\run_tests.bat`

## Script Windows

- `scripts/run_streamlit.bat`
  - Menjalankan Streamlit app baru (`apps/streamlit_app/app.py`).
- `scripts/run_api.bat`
  - Menjalankan FastAPI (`apps.api.main:app`).
- `scripts/run_tests.bat`
  - Menjalankan test suite (`pytest -q`).

## Catatan

- Arsitektur lama tetap tersedia untuk compatibility.
- `app.py` di root berstatus legacy/deprecated dan bukan launcher utama.
- Cache market, signal history, dan SQLite lokal ditulis ke `runtime/` agar repo tidak kotor oleh data hasil jalan aplikasi.
- Fokus produksi baru diarahkan ke layer `apps/ + services/ + domain/ + infrastructure/ + schemas/`.
- `apps/streamlit_app/ui/renderer_legacy.py` adalah renderer UI lama yang sudah tidak dipakai launcher utama; dipertahankan sementara untuk referensi migrasi.
- Untuk deploy Vercel, anggap root project `ai_trading_dashboard_prototipe` sebagai target utama sampai ada keputusan eksplisit untuk mengganti topology.
- `requirements.txt` sekarang backend-first untuk Vercel/API; `requirements-local.txt` dipakai untuk pengalaman Streamlit lokal.
- `requirements-api-local.txt` dipakai untuk runner FastAPI lokal.
