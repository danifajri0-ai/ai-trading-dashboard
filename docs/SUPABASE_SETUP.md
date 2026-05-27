# Supabase Setup (Optional Persistence Layer)

Dokumen ini menjelaskan cara menambahkan Supabase sebagai persistence tambahan tanpa memaksa auth/login dan tanpa mengubah UI Streamlit.

## 1) Prinsip Integrasi

- Supabase bersifat opsional.
- Jika env Supabase tidak lengkap atau `SUPABASE_ENABLED=false`, aplikasi tetap jalan.
- Endpoint analisis utama (`/analyze`, `/cockpit/analyze`) tetap bekerja.
- Persistence dipakai untuk history dan watchlist tambahan.

## 2) Environment Variables

Gunakan variabel berikut:

```env
SUPABASE_ENABLED=false
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=
```

Catatan:
- `SUPABASE_SERVICE_ROLE_KEY` dipakai backend untuk akses write/read table persistence.
- `SUPABASE_ANON_KEY` disiapkan untuk kebutuhan frontend masa depan (belum wajib dipakai sekarang).

## 3) Cara Buat Project Supabase

1. Buat project baru di Supabase.
2. Buka SQL Editor.
3. Jalankan script schema dari:
   - `supabase/migrations/0001_optional_persistence.sql`
   - `supabase/migrations/0002_multi_user_foundation.sql`
4. Ambil nilai:
   - Project URL -> `SUPABASE_URL`
   - Service role key -> `SUPABASE_SERVICE_ROLE_KEY`
   - Anon key -> `SUPABASE_ANON_KEY`
5. Simpan di environment lokal/hosting.

## 4) SQL Table yang Dibutuhkan

Tabel minimal:
- `analysis_logs`
- `watchlists`
- `user_profiles`
- `tier_limits`
- `user_usage_events`

SQL tersedia di:
- `supabase/migrations/0001_optional_persistence.sql`
- `supabase/migrations/0002_multi_user_foundation.sql`

Kolom utama:
- `analysis_logs`: `user_id`, `symbol`, `timeframe`, `signal`, `bias`, `confidence`, `summary`, `raw_payload`, `created_at`
- `watchlists`: `user_id`, `symbol`, `market_type`, `notes`, `created_at`
- `user_profiles`: `id`, `email`, `display_name`, `tier` (`free|plus|pro`), `is_active`, `created_at`, `updated_at`
- `tier_limits`: batas fitur per tier (`free`, `plus`, `pro`)
- `user_usage_events`: log event penggunaan per user untuk fondasi quota/billing

## 5) Cara Test Koneksi Lokal

1. Set env:
```env
SUPABASE_ENABLED=true
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
```

2. Jalankan API:
```powershell
venv\Scripts\python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```

3. Uji endpoint persistence:
- `POST /api/analysis/logs`
- `GET /api/analysis/history`
- `POST /api/watchlist`
- `GET /api/watchlist`
- `DELETE /api/watchlist/{id}`
- `POST /api/users/profile`
- `GET /api/users/profile/{user_id}`
- `GET /api/users/tier-limits`
- `POST /api/users/usage-events`

Jika konfigurasi valid, data akan tersimpan ke Supabase.

## 6) Cara Mematikan Supabase (Safe Fallback)

Untuk mematikan persistence tanpa mengganggu app:
```env
SUPABASE_ENABLED=false
```

Perilaku saat disabled:
- App tetap startup normal.
- Endpoint health tetap normal.
- Endpoint persistence memberi respons jelas bahwa Supabase disabled/unavailable.
- Endpoint analisis utama tetap berjalan.
