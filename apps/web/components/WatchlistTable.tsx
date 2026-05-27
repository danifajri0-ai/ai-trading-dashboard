import type { WatchlistItem } from "@/lib/types";

type WatchlistTableProps = {
  items: WatchlistItem[];
};

export function WatchlistTable({ items }: WatchlistTableProps) {
  return (
    <section className="card">
      <h3>Watchlist Table</h3>
      <p className="section-subtitle">Daftar pair prioritas untuk monitoring setup.</p>
      <table className="table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Market</th>
            <th>Notes</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {items.length === 0 ? (
            <tr>
              <td colSpan={4}>No watchlist items available.</td>
            </tr>
          ) : (
            items.map((item, idx) => (
              <tr key={item.id ?? `${item.symbol}-${idx}`}>
                <td>{item.symbol}</td>
                <td>{item.market_type}</td>
                <td>{item.notes || "-"}</td>
                <td>{new Date(item.created_at).toLocaleString()}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  );
}
