# Migration Strategy: Streamlit -> Render + Supabase + Vercel

Tujuan strategi ini adalah transisi bertahap tanpa merusak aplikasi yang berjalan.

Guardrails:
1. Streamlit tidak dihapus.
2. Tidak ada redesign UI besar di fase awal.
3. Tidak membuat Next.js dulu sebelum baseline UI + API stabil.
4. Logic analisis utama tetap dipertahankan (kecuali bug kecil yang jelas).

## 1) Prinsip Arsitektur Target

Target end-state:
- FastAPI di Render sebagai backend utama.
- Supabase sebagai storage + auth + logging.
- Next.js di Vercel sebagai mirror UI modern.
- Streamlit tetap aktif sebagai legacy/internal dashboard.

Prinsip operasional:
- FastAPI menjadi **single source of truth** untuk data analisis.
- Streamlit dan Next.js sama-sama konsumsi endpoint FastAPI yang sama.
- Perubahan schema dilakukan additive, bukan breaking.

## 2) Cara Supabase Masuk Tanpa Mengubah UI

Fase awal Supabase tidak menyentuh tampilan UI.

Strategi:
1. Tambahkan storage adapter di layer `infrastructure/` + pemanggilan dari `services/`.
2. Mulai dari write-path non-blocking:
   - log request analisis
   - log hasil ringkas/snapshot
   - audit event/error event
3. Jika Supabase gagal, alur analisis tetap berjalan (fail-open di jalur logging).
4. Auth bisa mulai sebagai optional (internal token/session), belum wajib untuk semua route.

Hasil: UI Streamlit tidak berubah, tetapi data operasional mulai terekam.

## 3) Cara FastAPI Menjadi Single Source of Truth

Kondisi saat ini:
- Streamlit bisa local service dan `http_api`.
- Endpoint inti sudah ada (`/analyze`, `/cockpit/analyze`, `/symbols`, `/health`).

Langkah stabilisasi:
1. Jadikan route FastAPI kontrak resmi untuk frontend.
2. Lock schema baseline:
   - `AnalysisResult`
   - `CockpitAnalysisResult`
3. Tambah metadata non-breaking (mis. request id, generated timestamp) bila perlu.
4. Pertahankan fallback local di Streamlit selama masa transisi.
5. Setelah backend stabil, mode default produksi beralih ke `http_api`.

## 4) Streamlit Tetap Aktif sebagai Legacy/Internal Dashboard

Peran Streamlit selama transisi:
- Dashboard internal operasional.
- Backup UI saat frontend mirror masih proses parity.
- Alat validasi cepat terhadap perubahan kontrak backend.

Kebijakan:
- Tidak menghapus panel baseline.
- Tidak refactor besar sebelum parity tercapai.
- Jika ada perubahan visual, hanya polish minor dan non-disruptive.

## 5) Strategi Smooth dari Streamlit ke Next.js

## Fase A - Baseline Lock (Audit)
- Dokumentasikan baseline UI dan API (sudah dilakukan).
- Pastikan test kontrak hijau.

## Fase B - Backend Hardening di Render
- Deploy FastAPI ke Render.
- Stabilkan endpoint dan observability.
- Pastikan Streamlit mode `http_api` stabil + fallback aman.

## Fase C - Supabase Foundation
- Integrasi logging/audit data via service layer.
- Tambah tabel minimal untuk event/analysis snapshot.
- Jangan ubah alur render UI.

## Fase D - Next.js Mirror (Parity First)
- Bangun UI berdasarkan baseline Streamlit, bukan redesign.
- Konsumsi endpoint yang sama.
- Verifikasi parity untuk section wajib: overview, signal/confidence, indicator, sentiment, risk, market context, setup strategy, selector.

## Fase E - Dual Run
- Streamlit dan Next.js berjalan paralel.
- Bandingkan availability, latency, dan parity output.
- Putuskan pergeseran traffic secara bertahap.

## 6) Roadmap Singkat Render + Vercel + Supabase

1. Minggu 1:
   - lock baseline docs + kontrak
   - hardening endpoint FastAPI
2. Minggu 2:
   - deploy FastAPI ke Render
   - setup Supabase project + tabel log minimal
3. Minggu 3:
   - sambungkan backend ke Supabase (non-blocking logging)
   - validasi test + smoke internal
4. Minggu 4:
   - mulai Next.js mirror di Vercel berbasis parity baseline
   - dual run terbatas untuk validasi

## 7) Risiko Migrasi Utama

1. Drift UI antara Streamlit dan Next.js.
   - Mitigasi: parity checklist berbasis baseline section.
2. Breaking response API saat refactor backend.
   - Mitigasi: contract tests wajib hijau.
3. Supabase jadi single point failure jika coupling terlalu kuat.
   - Mitigasi: logging non-blocking, bukan dependency hard di path analisis.
4. Perbedaan config env antar platform (local/Render/Vercel).
   - Mitigasi: `.env.example` jelas + verifikasi startup tiap target.

## 8) Definition of Done Audit Phase

Audit fase ini dianggap selesai jika:
1. Baseline UI terdokumentasi.
2. Baseline API contract terdokumentasi.
3. Strategi migrasi bertahap terdokumentasi.
4. Existing test tetap hijau.
5. Tidak ada perubahan besar pada UI/logic analisis.

