import type { AnalysisHistoryItem } from "@/lib/types";

type AnalysisHistoryProps = {
  items: AnalysisHistoryItem[];
};

export function AnalysisHistory({ items }: AnalysisHistoryProps) {
  return (
    <section className="card">
      <h3>Analysis History</h3>
      <p className="section-subtitle">Riwayat hasil analisa dari persistence layer.</p>
      <table className="table">
        <thead>
          <tr>
            <th>Created</th>
            <th>Symbol</th>
            <th>TF</th>
            <th>Signal</th>
            <th>Bias</th>
            <th>Confidence</th>
            <th>Summary</th>
          </tr>
        </thead>
        <tbody>
          {items.length === 0 ? (
            <tr>
              <td colSpan={7}>No analysis history available.</td>
            </tr>
          ) : (
            items.map((item, idx) => (
              <tr key={item.id ?? `${item.symbol}-${idx}`}>
                <td>{new Date(item.created_at).toLocaleString()}</td>
                <td>{item.symbol}</td>
                <td>{item.timeframe}</td>
                <td>{item.signal}</td>
                <td>{item.bias}</td>
                <td>{item.confidence.toFixed(1)}%</td>
                <td>{item.summary}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  );
}
