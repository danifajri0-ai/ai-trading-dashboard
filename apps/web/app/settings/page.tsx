export const metadata = {
  title: "Settings | AI Trading Dashboard"
};

export default function SettingsPage() {
  const apiConfigured = Boolean(process.env.NEXT_PUBLIC_API_BASE_URL);
  const supabaseUrlConfigured = Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL);
  const supabaseKeyConfigured = Boolean(process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY);

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
          <span>API Base URL Status</span>
          <strong>{apiConfigured ? "configured" : "not set (strict backend mode blocks live analysis)"}</strong>
        </div>
        <div className="kv">
          <span>Supabase URL Status</span>
          <strong>{supabaseUrlConfigured ? "configured" : "not set"}</strong>
        </div>
        <div className="kv">
          <span>Supabase Publishable Key</span>
          <strong>{supabaseKeyConfigured ? "configured" : "not set"}</strong>
        </div>
      </section>
    </main>
  );
}
