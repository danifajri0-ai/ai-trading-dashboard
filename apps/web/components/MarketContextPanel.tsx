type MarketContextPanelProps = {
  context?: Record<string, unknown> | null;
};

export function MarketContextPanel({ context }: MarketContextPanelProps) {
  const entries = Object.entries(context ?? {});
  return (
    <section className="card">
      <h3>Market Context</h3>
      <p className="section-subtitle">Context lite mirror dari payload analisis.</p>
      {entries.length === 0 ? (
        <p>Market context belum tersedia.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Field</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([key, value]) => (
              <tr key={key}>
                <td>{key}</td>
                <td>{typeof value === "object" ? JSON.stringify(value) : String(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
