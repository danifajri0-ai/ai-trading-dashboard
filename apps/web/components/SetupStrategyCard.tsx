type SetupStrategyCardProps = {
  signal: string;
  explanation?: string;
  reasons: string[];
  warnings: string[];
};

export function SetupStrategyCard({ signal, explanation, reasons, warnings }: SetupStrategyCardProps) {
  return (
    <section className="card">
      <h3>Setup Strategy</h3>
      <p className="section-subtitle">Mirror dari signal rationale dan warning streamlit.</p>
      <div className="metric" style={{ marginBottom: 10 }}>
        <span className="metric-label">Primary Action</span>
        <span className="metric-value">{signal}</span>
      </div>
      <p style={{ marginBottom: 12 }}>{explanation || "No explanation summary available."}</p>
      <h4 style={{ margin: "6px 0" }}>Reasons</h4>
      <ul style={{ marginTop: 6, paddingLeft: 18 }}>
        {reasons.length === 0 ? <li>No reasons available.</li> : reasons.map((reason) => <li key={reason}>{reason}</li>)}
      </ul>
      <h4 style={{ margin: "12px 0 6px" }}>Warnings</h4>
      <ul style={{ marginTop: 0, paddingLeft: 18 }}>
        {warnings.length === 0 ? <li>No warnings.</li> : warnings.map((warning) => <li key={warning}>{warning}</li>)}
      </ul>
    </section>
  );
}
