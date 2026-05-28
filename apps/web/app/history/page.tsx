import { headers } from "next/headers";

import { AnalysisHistory } from "@/components/AnalysisHistory";
import { buildServerApiRequestOptions, getHistory } from "@/lib/api";

export const metadata = {
  title: "History | AI Trading Dashboard"
};

export default async function HistoryPage() {
  const apiRequestOptions = buildServerApiRequestOptions(headers());
  const items = await getHistory(100, apiRequestOptions);

  return (
    <main className="grid" style={{ gap: 14 }}>
      <section className="card">
        <h2>Analysis History</h2>
        <p className="section-subtitle">
          Riwayat output analisa untuk audit keputusan dan evaluasi setup.
        </p>
      </section>
      <AnalysisHistory items={items} />
    </main>
  );
}
