type SentimentPanelProps = {
  label?: string;
  score?: number;
  source?: string;
  context?: string[];
};

export function SentimentPanel({ label, score, source, context }: SentimentPanelProps) {
  return (
    <section className="card">
      <h3>Sentiment Panel</h3>
      <div className="grid grid-3" style={{ marginBottom: 12 }}>
        <div className="metric">
          <span className="metric-label">Label</span>
          <span className="metric-value">{label ?? "-"}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Score</span>
          <span className="metric-value">{score !== undefined ? `${score.toFixed(1)}` : "-"}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Source</span>
          <span className="metric-value" style={{ fontSize: 16 }}>
            {source ?? "-"}
          </span>
        </div>
      </div>
      <p>{context && context.length > 0 ? context.join(" | ") : "Sentiment context belum tersedia."}</p>
    </section>
  );
}
