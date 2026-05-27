type IndicatorPanelProps = {
  trend?: string;
  emaFast?: number;
  emaSlow?: number;
  rsi?: number;
  atr?: number;
  support?: number;
  resistance?: number;
};

function fmt(value?: number): string {
  if (value === undefined || Number.isNaN(value)) return "-";
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function IndicatorPanel(props: IndicatorPanelProps) {
  const rows = [
    ["Trend", props.trend ?? "-"],
    ["EMA Fast", fmt(props.emaFast)],
    ["EMA Slow", fmt(props.emaSlow)],
    ["RSI", fmt(props.rsi)],
    ["ATR", fmt(props.atr)],
    ["Support", fmt(props.support)],
    ["Resistance", fmt(props.resistance)]
  ];
  return (
    <section className="card">
      <h3>Indicator Panel</h3>
      <p className="section-subtitle">Mirror dari ringkasan indikator Streamlit.</p>
      <table className="table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([name, value]) => (
            <tr key={name}>
              <td>{name}</td>
              <td>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
