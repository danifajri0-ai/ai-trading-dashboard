import { headers } from "next/headers";

import { AnalysisHistory } from "@/components/AnalysisHistory";
import type { AnalysisHistoryItem } from "@/lib/types";
import { buildServerApiRequestOptions, getHistory } from "@/lib/api";

export const metadata = {
  title: "History | AI Trading Dashboard"
};

export default async function HistoryPage() {
  const apiRequestOptions = buildServerApiRequestOptions(headers());
  let items: AnalysisHistoryItem[] = [];
  let loadError = "";

  try {
    items = await getHistory(100, apiRequestOptions);
  } catch (error) {
    const message = error instanceof Error ? error.message : "API response unavailable.";
    loadError = `Analysis history unavailable from backend. ${message}`;
  }

  return (
    <main className="grid" style={{ gap: 14 }}>
      <section className="card">
        <h2>Analysis History</h2>
        <p className="section-subtitle">
          Riwayat output analisa untuk audit keputusan dan evaluasi setup.
        </p>
      </section>
      {loadError ? (
        <section className="card">
          <h3>History Unavailable</h3>
          <p className="section-subtitle">
            Frontend tidak menampilkan mock data untuk history. Verifikasi status persistence backend, URL API, dan env production root project.
          </p>
          <p className="section-subtitle">{loadError}</p>
        </section>
      ) : null}
      {!loadError ? <AnalysisHistory items={items} /> : null}
    </main>
  );
}
