# AI Trading Dashboard

Streamlit dashboard untuk analisis market berbasis data Yahoo Finance. Dashboard ini menghitung EMA, RSI, ATR, support-resistance, market bias, signal score, dan risk plan sederhana.

## Fitur

- Multi-asset: BTC/USD, ETH/USD, XAU/USD, EUR/USD, GBP/USD, USD/JPY.
- Validasi kombinasi timeframe dan periode agar data Yahoo Finance lebih stabil.
- Chart TradingView-style dengan zoom, pan, crosshair, EMA, support, resistance, volume, dan panel RSI.
- Chart menyimpan posisi zoom/pan terakhir saat auto-refresh selama pair, periode, dan timeframe sama.
- Tombol Follow Latest dan Reset View untuk mengontrol perilaku chart saat market bergerak.
- Mode `Stable Realtime` memakai Plotly `uirevision` agar view lebih tahan saat auto-refresh.
- Auto-refresh sinyal berkala untuk mode near realtime.
- Signal score berbasis trend, RSI, lokasi harga, volatilitas, dan risk-reward.
- Risk plan dengan area entry, stop loss, take profit, dan rasio reward.
- Overview modern dengan warna dinamis, panah tick naik/turun, dan status live/manual.
- Panel detail untuk technical metrics, price action candle terakhir, market structure, risk, signal model, dan data integrity.
- Modul terpisah untuk data market, indikator teknikal, sinyal, dan konteks market.

## Tentang Realtime

Dashboard ini memakai Yahoo Finance lewat `yfinance`, jadi bukan feed broker tick-by-tick seperti MetaTrader. Mode auto-refresh memperbarui data, chart, dan sinyal secara berkala, tetapi data bisa delay, kosong, atau tidak berubah pada setiap refresh. Untuk eksekusi trading sungguhan, tetap validasi harga di broker.

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
