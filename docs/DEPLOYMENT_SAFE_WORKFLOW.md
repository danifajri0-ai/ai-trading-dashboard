# DEPLOYMENT SAFE WORKFLOW

## 1) Branching
1. Checkout branch baru dari branch stabil (mis. `main`):
   - `git checkout -b codex/<fitur-atau-fix>`
2. Jangan hapus/ubah flow legacy compatibility di root `app.py`.
3. Fokus perubahan di layer yang tepat:
   - `domain`, `services`, `schemas`, `apps/api`, `apps/streamlit_app`, `tests`.

## 2) Test (Wajib)
1. Jalankan test:
   - `pytest -q`
2. Jika gagal, perbaiki dulu sampai hijau sebelum lanjut.

## 3) Run Streamlit (Smoke Check UI)
1. Jalankan:
   - `streamlit run app.py`
2. Verifikasi cepat:
   - App bisa dibuka.
   - Alur analisa utama tetap jalan.
   - Tidak ada error fatal di startup.

## 4) Run API (Smoke Check Backend)
1. Jalankan:
   - `uvicorn apps.api.main:app --reload`
2. Verifikasi cepat:
   - `GET /health` respons OK.
   - `POST /analyze` tetap mengembalikan payload kompatibel.

## 5) Commit & Review
1. Commit kecil dan fokus.
2. Pastikan tidak ada perubahan destruktif pada file legacy.
3. Minta review untuk perubahan yang menyentuh kontrak schema/result.

## 6) Deploy
1. Deploy dari branch yang sudah lolos test + smoke check.
2. Monitor startup logs dan endpoint health.
3. Jika ada regresi, rollback ke release stabil terakhir.
