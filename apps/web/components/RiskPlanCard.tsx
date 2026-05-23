type RiskPlanCardProps = {
  riskLevel?: string;
  entryArea?: number | null;
  stopLoss?: number | null;
  takeProfit?: number | null;
  riskReward?: number | null;
  maxRiskPct?: number | null;
  notes?: string[];
};

function fmt(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) return "-";
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function RiskPlanCard(props: RiskPlanCardProps) {
  return (
    <section className="card">
      <h3>Risk Plan</h3>
      <div className="grid grid-3">
        <div className="metric">
          <span className="metric-label">Risk Level</span>
          <span className="metric-value">{props.riskLevel ?? "-"}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Entry</span>
          <span className="metric-value">{fmt(props.entryArea)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Stop Loss</span>
          <span className="metric-value">{fmt(props.stopLoss)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Take Profit</span>
          <span className="metric-value">{fmt(props.takeProfit)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">R:R</span>
          <span className="metric-value">{fmt(props.riskReward)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Max Risk %</span>
          <span className="metric-value">
            {props.maxRiskPct !== undefined && props.maxRiskPct !== null ? `${(props.maxRiskPct * 100).toFixed(2)}%` : "-"}
          </span>
        </div>
      </div>
      <p style={{ marginTop: 12 }}>{props.notes && props.notes.length > 0 ? props.notes.join(" | ") : "No risk notes."}</p>
    </section>
  );
}
