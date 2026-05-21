# AI Trading Dashboard

Streamlit dashboard untuk analisis market berbasis data publik. Dashboard ini menghitung EMA, RSI, ATR, support-resistance, market bias, signal score, dan risk plan dalam tampilan trading desk modern.

## Fitur

- Multi-asset: BTC/USD, ETH/USD, XAU/USD, EUR/USD, GBP/USD, USD/JPY.
- Validasi kombinasi timeframe dan periode agar data lebih stabil.
- Pro Chart dengan zoom, pan, crosshair, EMA, support, resistance, dan panel RSI.
- Chart menjaga posisi zoom/pan saat auto-refresh pada market dan timeframe yang sama.
- Refresh mode profesional: Smooth Refresh, Live Monitor, dan Manual Review.
- Crypto BTC/ETH mencoba Binance public klines tanpa API key, lalu fallback ke Yahoo Finance.
- Signal score berbasis trend, RSI, lokasi harga, volatilitas, dan risk-reward.
- Risk plan dengan area entry, stop loss, take profit, dan rasio reward.
- Overview modern dengan warna dinamis, panah tick naik/turun, dan status live/manual.
- Panel detail untuk technical metrics, price action candle terakhir, market structure, ICT framework, risk, signal model, dan data integrity.
- Modul terpisah untuk data market, indikator teknikal, sinyal, dan konteks market.

## Tentang Realtime

Dashboard ini memakai data publik. BTC/ETH mencoba Binance public klines tanpa API key; Forex/XAU memakai Yahoo Finance lewat `yfinance`. Ini belum setara broker tick feed seperti MetaTrader. Mode update memperbarui data, chart, dan sinyal secara berkala, tetapi data bisa delay, kosong, atau tidak berubah pada setiap refresh. Untuk eksekusi trading sungguhan, tetap validasi harga di broker.

## Deploy Streamlit Community Cloud

1. Push repository ke GitHub.
2. Buka Streamlit Community Cloud.
3. Pilih repository ini, branch `main`, dan main file `app.py`.
4. Deploy. Dependencies akan di-install dari `requirements.txt`.

File `.streamlit/config.toml` sudah disiapkan untuk tema dark profesional. Jangan commit file `.streamlit/secrets.toml`; gunakan Streamlit Secrets jika nanti menambahkan API token premium.

## Menjalankan Aplikasi

Cara paling mudah di Windows:

```text
Double click run_dashboard.bat
```

Cara manual:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Jika `venv` lama bermasalah, hapus atau rename folder `venv` lalu buat ulang dengan perintah di atas.

## Struktur

- `app.py`: UI Streamlit dan orchestration.
- `market_data.py`: pair, validasi request, download, dan normalisasi data.
- `technical_analysis.py`: EMA, RSI, ATR, trend, level, dan risk plan.
- `ai_signal.py`: scoring sinyal berbasis aturan.
- `sentiment_news.py`: konteks market dan checklist sebelum entry.

## Catatan

Dashboard ini hanya alat bantu analisis dan edukasi, bukan sinyal trading pasti. Tetap gunakan validasi price action, money management, dan kalender berita.
