type MarketHeaderProps = {
  symbol: string;
  timeframe: string;
  source: string;
};

export function MarketHeader({ symbol, timeframe, source }: MarketHeaderProps) {
  return (
    <section className="card">
      <p className="metric-label">Market Header</p>
      <h2 className="section-title" style={{ marginTop: 8 }}>
        {symbol} / {timeframe}
      </h2>
      <p className="section-subtitle">FastAPI source: {source}</p>
    </section>
  );
}
