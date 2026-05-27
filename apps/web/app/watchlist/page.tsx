import { WatchlistTable } from "@/components/WatchlistTable";
import { getWatchlist } from "@/lib/api";

export const metadata = {
  title: "Watchlist | AI Trading Dashboard"
};

export default async function WatchlistPage() {
  const items = await getWatchlist(100);

  return (
    <main className="grid" style={{ gap: 14 }}>
      <section className="card">
        <h2>Watchlist</h2>
        <p className="section-subtitle">
          Mirror daftar pair prioritas dari alur dashboard existing.
        </p>
      </section>
      <WatchlistTable items={items} />
    </main>
  );
}
