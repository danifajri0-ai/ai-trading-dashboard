# ROADMAP RICH AI COCKPIT (High-Level)

## Tujuan
Membangun Rich AI Trading Cockpit secara bertahap tanpa merusak flow Streamlit yang sudah berjalan, dengan backend/service sebagai sumber kebenaran data.

## Fase 1: Safety Baseline (Now)
- Kunci kontrak output analisa agar tetap kompatibel dengan UI.
- Kunci boundary arsitektur: domain tetap bebas dari Streamlit.
- Dokumentasikan workflow deployment aman.

## Fase 2: Service-First Expansion
- Tambah kapabilitas analisa di `services` + `domain` (bukan di UI).
- Definisikan/ekstensi schema hasil analisa di `schemas`.
- Jaga backward compatibility field yang sudah dipakai frontend.

## Fase 3: Rich Cockpit UI Incremental
- UI hanya render schema/result dari backend/service.
- Tambah panel/komponen baru secara bertahap di `apps/streamlit_app/ui`.
- Hindari rewrite besar; lakukan perubahan kecil dan terukur.

## Fase 4: Reliability & Ops
- Perkuat test regresi (service, API, UI helpers).
- Terapkan release workflow berbasis branch + verifikasi lokal.
- Deploy bertahap dengan rollback cepat jika anomali.

## Guardrails Non-Negotiable
- `app.py` root tetap dipertahankan untuk legacy compatibility.
- Domain tidak boleh import Streamlit.
- Frontend tidak membuat logika analisa inti; hanya konsumsi hasil backend/service.
