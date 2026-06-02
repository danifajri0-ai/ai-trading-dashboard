import { headers } from "next/headers";

import { buildServerApiRequestOptions, getApiConfigState, getApiHealth } from "@/lib/api";

export const metadata = {
  title: "Settings | AI Trading Dashboard"
};

export default async function SettingsPage() {
  const apiRequestOptions = buildServerApiRequestOptions(headers());
  const apiConfigState = getApiConfigState();
  const supabaseUrlConfigured = Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL);
  const supabaseKeyConfigured = Boolean(process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY);
  const requestTimeoutMs = resolveRequestTimeoutMs();
  let persistenceStatus = "unknown";
  let persistenceReason = "";

  try {
    const health = await getApiHealth(apiRequestOptions);
    persistenceStatus = health.persistence?.status || "unknown";
    persistenceReason = health.persistence?.reason || "";
  } catch (error) {
    const message = error instanceof Error ? error.message : "Health endpoint unavailable.";
    persistenceReason = `Backend health check unavailable. ${message}`;
  }

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
          <strong>
            {apiConfigState === "configured"
              ? "configured"
              : apiConfigState === "auto_vercel"
                ? "auto-detected from co-hosted Vercel deployment"
                : "not set (set API_BASE_URL or NEXT_PUBLIC_API_BASE_URL for separate Vercel web deploys)"}
          </strong>
        </div>
        <div className="kv">
          <span>Supabase URL Status</span>
          <strong>{supabaseUrlConfigured ? "configured" : "not set"}</strong>
        </div>
        <div className="kv">
          <span>Supabase Publishable Key</span>
          <strong>{supabaseKeyConfigured ? "configured" : "not set"}</strong>
        </div>
        <div className="kv">
          <span>API Request Timeout</span>
          <strong>{requestTimeoutMs}ms</strong>
        </div>
        <div className="kv">
          <span>Backend Persistence</span>
          <strong>{persistenceStatus}</strong>
        </div>
        {persistenceReason ? (
          <p className="section-subtitle">
            {persistenceReason}
          </p>
        ) : null}
      </section>
    </main>
  );
}

function resolveRequestTimeoutMs(): number {
  const configuredValue =
    process.env.API_REQUEST_TIMEOUT_MS?.trim() || process.env.NEXT_PUBLIC_API_REQUEST_TIMEOUT_MS?.trim();
  if (!configuredValue) {
    return 8000;
  }

  const parsedValue = Number(configuredValue);
  if (!Number.isFinite(parsedValue)) {
    return 8000;
  }

  return Math.max(1000, Math.min(parsedValue, 30000));
}
