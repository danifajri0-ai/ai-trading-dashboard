type SignalCardProps = {
  signal: string;
  bias: string;
  confidence: number;
  riskLevel: string;
};

function tone(value: string): "good" | "warn" | "bad" {
  const upper = value.toUpperCase();
  if (upper.startsWith("BUY") || upper.includes("BULL")) return "good";
  if (upper.startsWith("SELL") || upper.includes("BEAR")) return "bad";
  return "warn";
}

export function SignalCard({ signal, bias, confidence, riskLevel }: SignalCardProps) {
  return (
    <section className="card">
      <h3>Signal Decision</h3>
      <div className="grid grid-4">
        <div className="metric">
          <span className="metric-label">Signal</span>
          <span className="metric-value">{signal}</span>
          <span className={`pill ${tone(signal)}`}>{signal}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Bias</span>
          <span className="metric-value">{bias}</span>
          <span className={`pill ${tone(bias)}`}>{bias}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Confidence</span>
          <span className="metric-value">{confidence.toFixed(0)}%</span>
        </div>
        <div className="metric">
          <span className="metric-label">Risk Level</span>
          <span className="metric-value">{riskLevel}</span>
        </div>
      </div>
    </section>
  );
}
