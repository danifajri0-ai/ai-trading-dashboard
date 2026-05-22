# Architecture Layers (Phase 1)

Dokumen ini menjelaskan struktur baru untuk migrasi bertahap arsitektur trading dashboard.

Tujuan fase ini:
- Menyiapkan fondasi folder.
- Menjaga aplikasi lama tetap berjalan (`app.py` sebagai entrypoint utama).
- Menghindari perubahan behavior saat ini.

## Layer Overview

- `apps/streamlit_app/`
  - Tempat aplikasi Streamlit baru secara bertahap.
  - Fase awal: hanya skeleton package, belum menggantikan `app.py`.

- `apps/streamlit_app/ui/`
  - Komponen presentasi/UI (layout, chart renderer, styles).
  - Tidak menyimpan business rule inti.

- `apps/streamlit_app/client/`
  - Client adapter untuk akses service internal atau API backend di masa depan.
  - Dipakai saat transisi dari direct module call ke service call.

- `domain/`
  - Logika inti analisis (indikator, trend, signal, risk, backtest) yang bersifat pure domain.
  - Idealnya minim ketergantungan ke framework UI.

- `services/`
  - Orkestrasi use-case aplikasi.
  - Menjembatani UI dengan domain + provider data.

- `infrastructure/providers/`
  - Integrasi source eksternal (contoh: provider market data publik).
  - Berisi detail teknis akses API/SDK.

- `schemas/`
  - Kontrak data (DTO/schema) untuk pertukaran antar layer.
  - Menjaga konsistensi payload saat migrasi.

- `config/`
  - Konfigurasi aplikasi terpusat (env/config object/constants).
  - Mengurangi hardcoded config tersebar.

- `tests/`
  - Unit/integration test untuk layer baru.
  - Fase awal dapat dimulai dari test domain dan service.

## Migration Guardrails

- File lama **tidak dihapus**.
- Logic **tidak dipindah sekaligus**.
- `app.py` **tidak di-rewrite** dalam fase ini.
- Perubahan dilakukan inkremental per modul, dengan verifikasi behavior tetap sama.

