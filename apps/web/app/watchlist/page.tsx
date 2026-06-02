import { headers } from "next/headers";

import { WatchlistTable } from "@/components/WatchlistTable";
import type { WatchlistItem } from "@/lib/types";
import { buildServerApiRequestOptions, getWatchlist } from "@/lib/api";

export const metadata = {
  title: "Watchlist | AI Trading Dashboard"
};

export default async function WatchlistPage() {
  const apiRequestOptions = buildServerApiRequestOptions(headers());
  let items: WatchlistItem[] = [];
  let loadError = "";

  try {
    items = await getWatchlist(100, apiRequestOptions);
  } catch (error) {
    const message = error instanceof Error ? error.message : "API response unavailable.";
    loadError = `Watchlist unavailable from backend. ${message}`;
  }

  return (
    <main className="grid" style={{ gap: 14 }}>
      <section className="card">
        <h2>Watchlist</h2>
        <p className="section-subtitle">
          Mirror daftar pair prioritas dari alur dashboard existing.
        </p>
      </section>
      {loadError ? (
        <section className="card">
          <h3>Watchlist Unavailable</h3>
          <p className="section-subtitle">
            Frontend tidak menampilkan mock watchlist. Verifikasi status persistence backend, URL API, dan env production.
          </p>
          <p className="section-subtitle">{loadError}</p>
        </section>
      ) : null}
      {!loadError ? <WatchlistTable items={items} /> : null}
    </main>
  );
}
