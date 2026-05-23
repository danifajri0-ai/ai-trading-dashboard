export const metadata = {
  title: "Settings | AI Trading Dashboard"
};

export default function SettingsPage() {
  return (
    <main className="grid" style={{ gap: 14 }}>
      <section className="card">
        <h2>Settings</h2>
        <p className="section-subtitle">
          Konfigurasi frontend mirror untuk endpoint API dan mode operasi.
        </p>
      </section>
      <section className="card">
        <h3>Environment</h3>
        <div className="kv">
          <span>API Base URL</span>
          <strong>{process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000 (default fallback)"}</strong>
        </div>
        <div className="kv">
          <span>Supabase URL</span>
          <strong>{process.env.NEXT_PUBLIC_SUPABASE_URL || "not set"}</strong>
        </div>
        <div className="kv">
          <span>Supabase Publishable Key</span>
          <strong>{process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ? "configured" : "not set"}</strong>
        </div>
      </section>
    </main>
  );
}
