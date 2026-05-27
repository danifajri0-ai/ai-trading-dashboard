type ConfidenceMeterProps = {
  confidence: number;
  qualityScore: number;
};

export function ConfidenceMeter({ confidence, qualityScore }: ConfidenceMeterProps) {
  return (
    <section className="card">
      <h3>Confidence Meter</h3>
      <p className="section-subtitle">Signal confidence and trade quality snapshot.</p>
      <div className="metric" style={{ marginBottom: 12 }}>
        <span className="metric-label">Confidence</span>
        <span className="metric-value">{confidence.toFixed(0)}%</span>
        <div className="progress">
          <span style={{ width: `${Math.max(0, Math.min(100, confidence))}%` }} />
        </div>
      </div>
      <div className="metric">
        <span className="metric-label">Trade Quality</span>
        <span className="metric-value">{qualityScore.toFixed(0)}/100</span>
        <div className="progress">
          <span style={{ width: `${Math.max(0, Math.min(100, qualityScore))}%` }} />
        </div>
      </div>
    </section>
  );
}
