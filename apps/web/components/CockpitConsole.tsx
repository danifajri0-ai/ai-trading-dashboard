import type {
  BacktestSnapshot,
  CockpitAnalysisResult,
  DataQuality,
  EvidenceItem,
  EvidenceLayer,
  MarketOverview,
  MultiTimeframe,
  PriceSnapshot,
  RegimeAnalysis,
  RiskGate,
  RiskPlan,
  SentimentContext,
  SignalDecision,
  SymbolsPayload
} from "@/lib/types";
import { cloneElement, isValidElement } from "react";

type SelectorProps = {
  symbolsPayload: SymbolsPayload;
  selectedSymbol: string;
  selectedTimeframe: string;
};

export function PairTimeframeSelector({ symbolsPayload, selectedSymbol, selectedTimeframe }: SelectorProps) {
  const categories = symbolsPayload.categories ?? { all: symbolsPayload.symbols };

  return (
    <form className="selector-panel" action="/dashboard" method="get">
      <div>
        <span className="eyebrow">Market Universe</span>
        <strong>Pair and timeframe selector</strong>
      </div>
      <label>
        <span>Pair</span>
        <select name="symbol" defaultValue={selectedSymbol}>
          {Object.entries(categories).map(([group, symbols]) => (
            <optgroup key={group} label={labelize(group)}>
              {symbols.map((symbol) => (
                <option key={symbol} value={symbol}>
                  {symbol}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </label>
      <label>
        <span>Timeframe</span>
        <select name="timeframe" defaultValue={selectedTimeframe}>
          {symbolsPayload.timeframes.map((timeframe) => (
            <option key={timeframe} value={timeframe}>
              {timeframe}
            </option>
          ))}
        </select>
      </label>
      <button type="submit">Analyze</button>
    </form>
  );
}

export function CockpitConsole({ result, apiStatus }: { result: CockpitAnalysisResult; apiStatus: string }) {
  const dataMode = resolveDataMode(result);
  return (
    <main className="cockpit-page">
      <CommandHeader result={result} apiStatus={apiStatus} dataMode={dataMode} />
      {dataMode !== "live" ? <LiveGuardBanner result={result} /> : null}
      <DecisionMap result={result} dataMode={dataMode} />
      <PostChartSummary result={result} dataMode={dataMode} />

      <div className="cockpit-main-grid">
        <div className="stack">
          <MarketStateBoard overview={result.market_overview} signal={result.signal_decision} regime={result.regime_analysis} dataQuality={result.data_quality} riskGate={result.risk_gate} />
          <SignalCommandCenter signal={result.signal_decision} overview={result.market_overview} risk={result.risk_plan} gate={result.risk_gate} dataMode={dataMode} />
        </div>
        <RiskExecutionConsole risk={result.risk_plan} gate={result.risk_gate} dataMode={dataMode} />
      </div>

      <DeepAnalysisConsole result={result} dataMode={dataMode} />
    </main>
  );
}

function LiveGuardBanner({ result }: { result: CockpitAnalysisResult }) {
  return (
    <section className="live-guard-banner">
      <strong>Simulation Mode Active</strong>
      <p>
        Live execution guidance is locked because data source is fallback/mock. Verify API connectivity before treating this as tradable output.
      </p>
      <div className="badge-row">
        <Badge value={`Price source: ${fmt(result.price_snapshot?.price_source, "limited")}`} tone="warn" />
        <Badge value={`Data quality: ${fmt(result.data_quality?.status, "limited")}`} tone={statusTone(result.data_quality?.status)} />
        <Badge value={`Sentiment source: ${fmt(result.sentiment_context?.source, "limited")}`} tone="warn" />
      </div>
    </section>
  );
}

function CommandHeader({ result, apiStatus, dataMode }: { result: CockpitAnalysisResult; apiStatus: string; dataMode: string }) {
  const price = result.price_snapshot;
  const overview = result.market_overview;
  const signal = result.signal_decision;
  const data = result.data_quality;
  const gate = result.risk_gate;

  return (
    <section className="command-header">
      <div className="command-copy">
        <span className="eyebrow">Trading Desk Command Header</span>
        <h1>
          {result.symbol} / {result.timeframe}
        </h1>
        <div className="price-line">{fmt(price?.last_price, "Limited price")}</div>
        <p>
          Provider: {fmt(price?.price_source, apiStatus)} | Updated: {fmtDate(price?.updated_at)} | Profile: Rich Cockpit v2
        </p>
        <div className="badge-row">
          <Badge value={`Data Mode: ${dataMode}`} tone={dataMode === "live" ? "good" : "warn"} />
        </div>
        <div className="badge-row">
          <Badge value={overview?.signal} tone={signalTone(overview?.signal)} />
          <Badge value={overview?.bias} tone={signalTone(overview?.bias)} />
          <Badge value={overview?.status} tone={statusTone(overview?.status)} />
        </div>
      </div>
      <div className="command-grid">
        <StatusChip label="Signal" value={overview?.signal} tone={signalTone(overview?.signal)} />
        <StatusChip label="Bias" value={overview?.bias} tone={signalTone(overview?.bias)} />
        <StatusChip label="Confidence" value={pctLabel(overview?.confidence)} tone="info" note="baseline" />
        <StatusChip label="Validation" value={pctLabel(signal?.validation_score, "limited")} tone={statusTone(signal?.status)} note="baseline" />
        <StatusChip label="Data Quality" value={pctLabel(data?.score, data?.status)} tone={statusTone(data?.status)} note="baseline" />
        <StatusChip label="Risk Gate" value={gate?.risk_status ?? gate?.status} tone={riskTone(gate?.risk_status)} />
        <StatusChip label="Price Feed" value={price?.status} tone={statusTone(price?.status)} />
        <StatusChip label="API" value={apiStatus} tone={apiStatus === "configured" ? "good" : "warn"} />
      </div>
    </section>
  );
}

function DecisionMap({ result, dataMode }: { result: CockpitAnalysisResult; dataMode: string }) {
  const price = result.price_snapshot;
  const overview = result.market_overview;
  const risk = result.risk_plan;
  const gate = result.risk_gate;
  const structure = result.market_structure;
  const data = result.data_quality;
  const levels = [structure?.support, risk?.stop_loss, price?.last_price, risk?.entry_area, risk?.take_profit, structure?.resistance]
    .filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  const { low, high } = rangeFor(levels);

  return (
    <section className="decision-map">
      <div className="map-head">
        <div>
          <span>Decision Map</span>
          <strong>
            {result.symbol} / {result.timeframe}
          </strong>
        </div>
        <div className="badge-row">
          <Badge value={price?.status} tone={statusTone(price?.status)} />
          <Badge value={overview?.bias} tone={signalTone(overview?.bias)} />
        </div>
      </div>
      <div className="map-toolbar">
        <Badge value={`Signal: ${fmt(overview?.signal, "limited")}`} tone={signalTone(overview?.signal)} />
        <Badge value={`Bias: ${fmt(overview?.bias, "limited")}`} tone={signalTone(overview?.bias)} />
        <Badge value={`Risk Gate: ${fmt(gate?.risk_status ?? gate?.status, "limited")}`} tone={riskTone(gate?.risk_status)} />
        <Badge value={`Data: ${fmt(data?.status, "limited")}`} tone={statusTone(data?.status)} />
        <Badge value={`Execution: ${dataMode === "live" ? "live" : "simulation_only"}`} tone={dataMode === "live" ? "good" : "warn"} />
      </div>
      <div className="map-price-row">
        <div>
          <div className="map-price">{fmt(price?.last_price, "Limited data")}</div>
          <DeltaTile label="Price vs Entry" current={price?.last_price} target={risk?.entry_area} />
        </div>
        <div className={`direction-card tone-${signalTone(overview?.signal ?? overview?.bias)}`}>
          <span>{directionLabel(overview)}</span>
          <strong>{directionArrow(overview)}</strong>
        </div>
      </div>
      <p>Decision map uses available price, support, resistance, entry, stop, and target levels.</p>
      <div className="price-map">
        <SignalZone entry={risk?.entry_area} stop={risk?.stop_loss} target={risk?.take_profit} low={low} high={high} />
        <LevelMarker label="Resistance" value={structure?.resistance} low={low} high={high} tone="bad" />
        <LevelMarker label="Target" value={risk?.take_profit} low={low} high={high} tone="good" />
        <LevelMarker label="Entry Zone" value={risk?.entry_area} low={low} high={high} tone="info" />
        <LevelMarker label="Current Price" value={price?.last_price} low={low} high={high} tone="neutral" />
        <LevelMarker label="Stop Loss" value={risk?.stop_loss} low={low} high={high} tone="bad" />
        <LevelMarker label="Support" value={structure?.support} low={low} high={high} tone="good" />
        <div className="map-gridline" />
      </div>
      <div className="distance-grid">
        <DeltaTile label="Distance to Entry" current={price?.last_price} target={risk?.entry_area} />
        <DeltaTile label="Distance to Stop" current={price?.last_price} target={risk?.stop_loss} />
        <DeltaTile label="Distance to Target" current={price?.last_price} target={risk?.take_profit} />
      </div>
    </section>
  );
}

function PostChartSummary({ result, dataMode }: { result: CockpitAnalysisResult; dataMode: string }) {
  const signal = result.signal_decision;
  const overview = result.market_overview;
  const risk = result.risk_plan;
  const gate = result.risk_gate;
  const mode = executionMode(signal, gate, dataMode);
  const invalidation = invalidationText(signal, risk);

  return (
    <section className="post-chart-grid">
      <article className="summary-card">
        <CardTitle label="Live Trade Brief" value={signal?.action ?? overview?.signal} />
        <div className="readiness">
          <div>
            <span>Trade Readiness</span>
            <strong>{readinessLabel(overview?.trade_quality_score)}</strong>
          </div>
          <Progress value={overview?.trade_quality_score} />
        </div>
        <div className="mini-grid">
          <Metric label="Entry" value={risk?.entry_area ?? "limited"} />
          <Metric label="Stop Loss" value={risk?.stop_loss ?? "limited"} tone="bad" />
          <Metric label="Take Profit" value={risk?.take_profit ?? "limited"} tone="good" />
          <Metric label="R:R" value={risk?.risk_reward ?? "limited"} tone="info" />
          <Metric label="Trade Readiness" value={dataMode === "live" ? readinessLabel(overview?.trade_quality_score) : "simulation_only"} tone={dataMode === "live" ? "info" : "warn"} />
          <Metric label="Risk Gate" value={gate?.risk_status ?? gate?.status ?? "limited"} tone={riskTone(gate?.risk_status)} />
        </div>
        <ChecklistItem label="Next Action" value={nextAction(mode, signal, gate)} tone={riskTone(mode)} />
        <ChecklistItem label="Invalidation" value={invalidation} tone={riskTone(gate?.risk_status)} />
      </article>
      <article className="summary-card">
        <CardTitle label="Risk Snapshot" value={gate?.risk_status ?? gate?.status ?? "limited"} />
        <div className="mini-grid">
          <Metric label="Entry" value={risk?.entry_area ?? "limited"} />
          <Metric label="Stop" value={risk?.stop_loss ?? "limited"} tone="bad" />
          <Metric label="Target" value={risk?.take_profit ?? "limited"} tone="good" />
          <Metric label="R:R" value={risk?.risk_reward ?? "limited"} tone="info" />
          <Metric label="Max Risk" value={maxRiskLabel(risk?.max_risk_pct)} tone={riskTone(risk?.risk_level)} />
          <Metric label="Risk Level" value={risk?.risk_level ?? "limited"} tone={riskTone(risk?.risk_level)} />
        </div>
      </article>
      <article className="summary-card">
        <CardTitle label="Setup Checklist" value={mode} />
        <ChecklistItem label="Execution" value={mode} tone={riskTone(mode)} />
        <ChecklistItem label="Risk Gate" value={gate?.risk_status ?? gate?.status ?? "limited"} tone={riskTone(gate?.risk_status)} />
        <ChecklistItem label="Validation" value={signal?.status ?? "limited"} tone={statusTone(signal?.status)} />
        <ChecklistItem label="Invalidation" value={invalidation} tone={riskTone(gate?.risk_status)} />
      </article>
    </section>
  );
}

function MarketStateBoard({
  overview,
  signal,
  regime,
  dataQuality,
  riskGate
}: {
  overview?: MarketOverview;
  signal?: SignalDecision;
  regime?: RegimeAnalysis;
  dataQuality?: DataQuality;
  riskGate?: RiskGate;
}) {
  return (
    <section className="terminal-panel">
      <SectionTitle eyebrow="Market Overview" title="Market State Board" meta={overview?.summary ?? "Live market state from cockpit schema"} />
      <div className="state-board">
        <StateCard title="Trend Pressure" value={trendRead(overview).toUpperCase()} status={overview?.status} note={trendNote(overview)} tone={signalTone(overview?.bias)} size="wide" />
        <StateCard title="Momentum" value={momentumValue(signal).toUpperCase()} status="limited" note={signal?.confirmation_reason ?? signal?.warning_reason ?? "Momentum detail is limited."} tone={statusTone("limited")} size="wide" />
        <StateCard title="Volatility" value={fmt(regime?.volatility_state, "LIMITED DATA").toUpperCase()} status={regime?.status} note={volatilityNote(regime?.volatility_state)} tone={statusTone(regime?.status)} size="compact" />
        <StateCard title="Execution Quality" value={`${scoreGrade(overview?.trade_quality_score)} GRADE`} status={riskGate?.risk_status ?? riskGate?.status} note={`${scoreGrade(overview?.trade_quality_score)} setup quality with ${fmt(riskGate?.risk_status ?? riskGate?.status, "limited")} gate state.`} tone={riskTone(riskGate?.risk_status)} size="compact" />
        <StateCard title="Data Health" value={dataHealth(dataQuality).toUpperCase()} status={dataQuality?.status} note={first(dataQuality?.issues) ?? "Data is usable for this cockpit view."} tone={statusTone(dataQuality?.status)} size="compact" />
      </div>
      <p className="panel-note">{overview?.summary ?? "Ringkasan market belum tersedia."}</p>
    </section>
  );
}

function SignalCommandCenter({ signal, overview, risk, gate, dataMode }: { signal?: SignalDecision; overview?: MarketOverview; risk?: RiskPlan; gate?: RiskGate; dataMode: string }) {
  const mode = executionMode(signal, gate, dataMode);
  return (
    <section className="terminal-panel">
      <SectionTitle eyebrow="Decision Layer" title="Signal Command Center" meta="Primary action, validation, and execution readiness" />
      <div className="decision-layout">
        <div className="decision-block">
          <span className="cockpit-label">Primary Action</span>
          <div className={`decision-hero tone-${signalTone(signal?.action)}`}>{fmt(signal?.action, "limited")}</div>
          <div className="badge-row">
            <Badge value={signal?.status} tone={statusTone(signal?.status)} />
            <Badge value={mode} tone={riskTone(mode)} />
          </div>
          <p>Bias: {fmt(signal?.bias)} | Gate: {fmt(gate?.risk_status ?? gate?.status, "not_available")} | Mode: {dataMode === "live" ? "live" : "simulation_only"}</p>
          <Progress value={signal?.validation_score ?? signal?.confidence} />
        </div>
        <div className="decision-block">
          <div className="mini-grid two">
            <Metric label="Execution Mode" value={mode} tone={riskTone(mode)} />
            <Metric label="Trade Quality" value={overview?.trade_quality_score} tone="info" />
          </div>
          <ChecklistItem label="Confirmation Reason" value={signal?.confirmation_reason ?? "Limited data"} tone={statusTone(signal?.status)} />
          <ChecklistItem label="Warning" value={signal?.warning_reason ?? "No active warning"} tone={signal?.warning_reason ? "warn" : "neutral"} />
          <ChecklistItem label="Blocker" value={signal?.blocked_reason ?? "No active blocker"} tone={signal?.blocked_reason ? "bad" : "neutral"} />
        </div>
      </div>
      <div className="mini-grid three">
        <Metric label="Execution Mode" value={mode} tone={riskTone(mode)} />
        <Metric label="Trade Quality" value={dataMode === "live" ? overview?.trade_quality_score : "simulation_only"} tone={dataMode === "live" ? "info" : "warn"} />
        <Metric label="Valid Signal" value={validLabel(signal?.valid_signal)} tone={statusTone(signal?.status)} />
      </div>
      <ListBlock title="Why this signal" items={signal?.reasons} empty="Belum ada rationale." />
      <div className="signal-mini-grid">
        <ChecklistItem label="Confirmation" value={confirmationNeeded(signal)} tone={statusTone(signal?.status)} />
        <ChecklistItem label="Invalidation" value={invalidationText(signal, risk)} tone={riskTone(gate?.risk_status)} />
        <ChecklistItem label="Risk Gate" value={gate?.risk_status ?? gate?.status ?? "not_available"} tone={riskTone(gate?.risk_status)} />
      </div>
    </section>
  );
}

function RiskExecutionConsole({ risk, gate, dataMode }: { risk?: RiskPlan; gate?: RiskGate; dataMode: string }) {
  return (
    <section className="terminal-panel sticky-panel">
      <SectionTitle eyebrow="Execution Guardrails" title="Risk Execution Console" meta="Entry, stop, target, R:R, and gate state" />
      <div className="risk-rail">
        <div className="risk-grid">
          <Metric label="Entry Area" value={risk?.entry_area} />
          <Metric label="Stop Loss" value={risk?.stop_loss} tone="bad" />
          <Metric label="Take Profit" value={risk?.take_profit} tone="good" />
        </div>
        <div className="risk-profile">
          <span className="cockpit-label">Risk Reward Profile</span>
          <div className="risk-value">{fmt(risk?.risk_reward, "Limited data")} R</div>
          <Progress value={rrProgress(risk?.risk_reward)} />
          <div className="rr-labels">
            <span>poor</span>
            <span>tradable</span>
            <span>premium</span>
          </div>
        </div>
        <div className="risk-gate-grid">
          <Metric label="Risk Gate" value={gate?.risk_status ?? gate?.status ?? "not_available"} tone={riskTone(gate?.risk_status)} />
          <Metric label="Max Risk" value={maxRiskLabel(risk?.max_risk_pct)} tone={riskTone(risk?.risk_level)} />
          <Metric label="Risk Level" value={dataMode === "live" ? risk?.risk_level : "simulation_only"} tone={dataMode === "live" ? riskTone(risk?.risk_level) : "warn"} />
        </div>
        <div className="badge-row">
          <Badge value={risk?.status} tone={statusTone(risk?.status)} />
          <Badge value={gate?.risk_status ?? gate?.status ?? "not_available"} tone={riskTone(gate?.risk_status)} />
        </div>
      </div>
      <ListBlock title="Risk notes" items={[...(risk?.notes ?? []), ...(gate?.reasons ?? [])]} empty="No risk notes available for this setup." />
    </section>
  );
}

function DeepAnalysisConsole({ result, dataMode }: { result: CockpitAnalysisResult; dataMode: string }) {
  const orderedSections = resolveDeepSectionOrder(result);
  const sectionMap = buildDeepSectionMap(result);
  return (
    <section className="deep-console">
      <SectionTitle eyebrow="Evidence Workspace" title="Deep Analysis Console" meta="Evidence, heatmap, regime, data, and validation context" />
      <div className="tab-strip">
        {orderedSections.map((tab) => (
          <span key={tab}>{tab}</span>
        ))}
      </div>
      <div className="deep-grid">
        {orderedSections.map((section) => {
          const node = sectionMap[section];
          if (!node) {
            return null;
          }
          return isValidElement(node) ? cloneElement(node, { key: section }) : null;
        })}
        {dataMode !== "live" ? (
          <article className="analysis-panel">
            <CardTitle label="Live Guard" value="simulation_only" />
            <ListBlock
              title="Action lock"
              items={[
                "Execution guidance remains non-live until fallback/mock sources are cleared.",
                "Use this view for structure validation, UI parity, and workflow rehearsal only."
              ]}
              empty=""
            />
          </article>
        ) : null}
      </div>
    </section>
  );
}

function MarketContextPanel({ result }: { result: CockpitAnalysisResult }) {
  const context = result.market_context?.context ?? {};
  const entries = Object.entries(context);
  return (
    <article className="analysis-panel">
      <CardTitle label="Market Context" value={result.market_context?.status ?? "limited"} />
      <div className="mini-grid two">
        <Metric label="Data Mode" value={resolveDataMode(result)} tone={resolveDataMode(result) === "live" ? "good" : "warn"} />
        <Metric label="Source" value={result.price_snapshot?.price_source ?? "limited"} tone={statusTone(result.price_snapshot?.status)} />
      </div>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Context Field</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {entries.length ? entries.map(([key, value]) => (
              <tr key={key}>
                <td>{labelize(key)}</td>
                <td>{fmtContextValue(value)}</td>
              </tr>
            )) : (
              <tr><td colSpan={2}>Market context is currently unavailable.</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <ListBlock title="Context notes" items={result.market_context?.notes} empty="No context notes provided." />
    </article>
  );
}

function ValidationPanel({ result }: { result: CockpitAnalysisResult }) {
  return (
    <article className="analysis-panel span-2">
      <CardTitle label="Validation & Section Contract" value={result.validation_notes?.status ?? "limited"} />
      <div className="mini-grid three">
        <Metric label="Schema" value={result.schema_version ?? "limited"} tone="info" />
        <Metric label="UI Sections" value={result.ui_sections?.order?.length ?? 0} tone={statusTone(result.ui_sections?.status)} />
        <Metric label="Feature Flags" value={Object.keys(result.feature_flags ?? {}).length} tone="info" />
      </div>
      <ListBlock title="Validation notes" items={result.validation_notes?.notes} empty="No validation notes provided." />
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Section</th>
              <th>Visible</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {(result.ui_sections?.order ?? []).length ? (result.ui_sections?.order ?? []).map((section) => (
              <tr key={section}>
                <td>{section}</td>
                <td>{result.ui_sections?.visible?.[section] === false ? "false" : "true"}</td>
                <td>{sectionRole(section)}</td>
              </tr>
            )) : (
              <tr><td colSpan={3}>Section contract is currently unavailable.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </article>
  );
}

function EvidencePanel({ evidence }: { evidence?: EvidenceLayer }) {
  return (
    <article className="analysis-panel span-2">
      <CardTitle label="Evidence Layer" value={evidence?.status ?? "limited"} />
      <div className="evidence-grid">
        <EvidenceGroup title="Technical Evidence" rows={evidence?.technical_evidence} />
        <EvidenceGroup title="Risk Evidence" rows={evidence?.risk_evidence} />
        <EvidenceGroup title="Data Quality Evidence" rows={evidence?.data_quality_evidence} />
        <EvidenceGroup title="Contradictions" rows={evidence?.contradictions} />
      </div>
    </article>
  );
}

function HeatmapPanel({ confidence }: { confidence?: CockpitAnalysisResult["confidence_breakdown"] }) {
  const entries = Object.entries(confidence?.components ?? {});
  return (
    <article className="analysis-panel span-2">
      <CardTitle label="Signal Heatmap" value={pctLabel(confidence?.overall_score, "limited")} />
      <div className="heat-summary">
        <Badge value={confidence?.status} tone={statusTone(confidence?.status)} />
        <Metric label="Overall Score" value={confidence?.overall_score ?? "limited"} tone="info" />
        <Metric label="Grade" value={scoreGrade(confidence?.overall_score)} />
      </div>
      {entries.length ? (
        entries.map(([name, item]) => <HeatRow key={name} name={name} item={item} />)
      ) : (
        <p className="panel-note">Confidence contribution detail is limited for this analysis.</p>
      )}
    </article>
  );
}

function MtfPanel({ mtf }: { mtf?: MultiTimeframe }) {
  const biases = Object.entries(mtf?.per_timeframe_bias ?? {});
  return (
    <article className="analysis-panel">
      <CardTitle label="Multi-Timeframe" value={mtf?.status ?? "limited"} />
      <div className="mini-grid three">
        <Metric label="Alignment" value={mtf?.alignment_score ?? "limited"} tone={statusTone(mtf?.status)} />
        <Metric label="Dominant Bias" value={mtf?.dominant_bias ?? "limited"} tone="info" />
        <Metric label="Entry Timing" value={mtf?.entry_timing ?? "limited"} />
      </div>
      <Progress value={mtf?.alignment_score} />
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Timeframe</th>
              <th>Bias</th>
            </tr>
          </thead>
          <tbody>
            {biases.length ? biases.map(([timeframe, bias]) => (
              <tr key={timeframe}>
                <td>{timeframe}</td>
                <td>{bias}</td>
              </tr>
            )) : (
              <tr><td colSpan={2}>MTF detail unavailable.</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <ListBlock title="Conflict notes" items={mtf?.conflict_notes ?? mtf?.notes} empty="Tidak ada conflict note." />
    </article>
  );
}

function RegimePanel({ regime, structure }: { regime?: RegimeAnalysis; structure?: CockpitAnalysisResult["market_structure"] }) {
  return (
    <article className="analysis-panel">
      <CardTitle label="Regime & Structure" value={regime?.status ?? "limited"} />
      <div className="mini-grid two">
        <Metric label="Regime" value={regime?.regime ?? "limited"} tone={statusTone(regime?.status)} />
        <Metric label="Score" value={regime?.regime_score ?? "limited"} tone="info" />
        <Metric label="Strategy" value={regime?.preferred_strategy ?? "limited"} />
        <Metric label="Structure" value={structure?.structure ?? "limited"} tone={statusTone(structure?.status)} />
      </div>
      <Progress value={regime?.regime_score} />
      <ListBlock title="Regime notes" items={[...(regime?.notes ?? []), ...(structure?.notes ?? [])]} empty="Belum ada catatan." />
    </article>
  );
}

function DataQualityPanel({ quality }: { quality?: DataQuality }) {
  return (
    <article className="analysis-panel">
      <CardTitle label="Data Quality" value={quality?.status ?? "limited"} />
      <div className="mini-grid three">
        <Metric label="Score" value={quality?.score ?? "limited"} tone={statusTone(quality?.status)} />
        <Metric label="Freshness" value={quality?.freshness_status ?? "limited"} tone={statusTone(quality?.freshness_status)} />
        <Metric label="Source" value={String(quality?.raw?.source ?? "limited")} tone={statusTone(quality?.status)} />
      </div>
      <Progress value={quality?.score} />
      <ListBlock title="Issues" items={quality?.issues} empty="Tidak ada issue data quality." />
    </article>
  );
}

function BacktestPanel({ snapshot }: { snapshot?: BacktestSnapshot }) {
  const backtest = snapshot?.metrics?.backtest ?? {};
  const memory = snapshot?.metrics?.performance_memory ?? {};
  return (
    <article className="analysis-panel">
      <CardTitle label="Backtest Snapshot" value={snapshot?.status ?? "limited"} />
      <div className="mini-grid two">
        <Metric label="Sample" value={backtest.sample_size ?? "limited"} tone="info" />
        <Metric label="Est. Win Rate" value={backtest.estimated_win_rate ?? "limited"} tone="warn" />
        <Metric label="Avg R:R" value={backtest.avg_rr ?? "limited"} tone="info" />
        <Metric label="DD Estimate" value={backtest.max_drawdown_estimate ?? "limited"} tone="warn" />
        <Metric label="Memory" value={memory.sample_size ?? "limited"} tone={statusTone(memory.status)} />
      </div>
      <ListBlock title="Caveats" items={snapshot?.notes} empty="Backtest belum tersedia." />
    </article>
  );
}

function SentimentPanel({ sentiment }: { sentiment?: SentimentContext }) {
  return (
    <article className="analysis-panel">
      <CardTitle label="Sentiment Context" value={sentiment?.status ?? "limited"} />
      <div className="mini-grid three">
        <Metric label="Label" value={sentiment?.sentiment_label ?? "limited"} tone={signalTone(sentiment?.sentiment_label)} />
        <Metric label="Score" value={sentiment?.sentiment_score ?? "limited"} tone="info" />
        <Metric label="Source" value={sentiment?.source ?? "limited"} />
      </div>
      <Progress value={sentiment?.sentiment_score} />
      <ListBlock title="Context & caveat" items={[...(sentiment?.context ?? []), ...(sentiment?.notes ?? [])]} empty="Sentiment belum tersedia." />
    </article>
  );
}

function RadarDecisionPanel({ mtf, signal, gate, quality }: { mtf?: MultiTimeframe; signal?: SignalDecision; gate?: RiskGate; quality?: DataQuality }) {
  const rows = Object.entries(mtf?.per_timeframe_bias ?? {});
  const ready = signal?.valid_signal && gate?.risk_status === "valid" ? "Ready" : "Wait / Review";
  return (
    <article className="analysis-panel span-2">
      <CardTitle label="Radar & Decision Lab" value={ready} />
      <div className="radar-grid">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Timeframe</th>
                <th>Bias</th>
                <th>Dominant</th>
                <th>Entry Timing</th>
              </tr>
            </thead>
            <tbody>
              {rows.length ? rows.map(([timeframe, bias]) => (
                <tr key={timeframe}>
                  <td>{timeframe}</td>
                  <td>{bias}</td>
                  <td>{mtf?.dominant_bias ?? "limited"}</td>
                  <td>{mtf?.entry_timing ?? "limited"}</td>
                </tr>
              )) : (
                <tr><td colSpan={4}>Market radar is currently unavailable.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="mini-grid two">
          <Metric label="Action" value={signal?.action ?? "limited"} tone="info" />
          <Metric label="Signal Valid" value={validLabel(signal?.valid_signal)} tone={signal?.valid_signal ? "good" : "warn"} />
          <Metric label="Risk Gate" value={gate?.risk_status ?? "limited"} tone={statusTone(gate?.risk_status)} />
          <Metric label="Data" value={quality?.status ?? "limited"} tone={statusTone(quality?.status)} />
        </div>
      </div>
    </article>
  );
}

function EvidenceGroup({ title, rows }: { title: string; rows?: EvidenceItem[] }) {
  const cleanRows = rows?.length ? rows : [{ label: "Limited data", status: "limited", detail: emptyEvidenceCopy(title), score: null }];
  return (
    <div className="evidence-card">
      <div className="topline">
        <h4>{title}</h4>
        <Badge value={groupStatus(cleanRows)} tone={statusTone(groupStatus(cleanRows))} />
      </div>
      <p>{cleanRows.length} evidence item(s) available for trade review.</p>
      {cleanRows.slice(0, 3).map((row, index) => (
        <div className="evidence-item" key={`${title}-${index}`}>
          <strong>
            {fmt(row.label, "Evidence")} <Badge value={row.status} tone={statusTone(row.status)} />
          </strong>
          <small>{fmt(row.detail, "No detail")}{row.score !== null && row.score !== undefined ? ` | Score ${fmt(row.score)}` : ""}</small>
        </div>
      ))}
    </div>
  );
}

function HeatRow({ name, item }: { name: string; item: Record<string, unknown> }) {
  const score = numberOrNull(item.score);
  const weight = numberOrNull(item.weight);
  const weighted = numberOrNull(item.weighted_score);
  const maxWeighted = weight ? weight * 100 : null;
  const contribution = weighted !== null && maxWeighted ? (weighted / maxWeighted) * 100 : 0;
  return (
    <div className="heat-row">
      <div>
        <span>Component</span>
        <strong>{componentLabel(name)}</strong>
      </div>
      <div>
        <span>Weighted Contribution</span>
        <Progress value={contribution} />
      </div>
      <div>
        <span>Score</span>
        <strong>{fmt(score)}</strong>
      </div>
      <div>
        <span>Weight</span>
        <strong>{weight !== null ? `${Math.round(weight * 100)}%` : "Limited data"}</strong>
      </div>
      <div>
        <span>Weighted</span>
        <strong>{fmt(weighted)}</strong>
      </div>
    </div>
  );
}

function SectionTitle({ eyebrow, title, meta }: { eyebrow: string; title: string; meta?: string }) {
  return (
    <div className="cockpit-section-title">
      <div>
        <span>{eyebrow}</span>
        <strong>{title}</strong>
      </div>
      {meta ? <em>{meta}</em> : null}
    </div>
  );
}

function StateCard({ title, value, status, note, tone, size }: { title: string; value: string; status?: unknown; note: string; tone: string; size: string }) {
  return (
    <div className={`state-card state-${size} tone-${tone}`}>
      <div className="topline">
        <h4>{title}</h4>
        <Badge value={status ?? "not_available"} tone={statusTone(status)} />
      </div>
      <span className="state-value">{value}</span>
      <div className="delta-pill">
        <span>Delta</span>
        <strong>baseline</strong>
      </div>
      <p>{note}</p>
    </div>
  );
}

function Metric({ label, value, tone = "neutral" }: { label: string; value: unknown; tone?: string }) {
  return (
    <div className={`cockpit-metric tone-${tone}`}>
      <span className="cockpit-label">{label}</span>
      <span className="cockpit-value">{fmt(value, "Limited data")}</span>
    </div>
  );
}

function StatusChip({ label, value, tone = "neutral", note }: { label: string; value: unknown; tone?: string; note?: string }) {
  return (
    <div className={`status-chip tone-${tone}`}>
      <span>{label}</span>
      <strong>{fmt(value, "Limited data")}</strong>
      {note ? <small>{note}</small> : null}
    </div>
  );
}

function Badge({ value, tone = "neutral" }: { value: unknown; tone?: string }) {
  return <span className={`cockpit-badge tone-${tone}`}>{fmt(value, "Limited data")}</span>;
}

function Progress({ value }: { value: unknown }) {
  return (
    <div className="cockpit-bar">
      <div className="cockpit-fill" style={{ width: `${clamp(numberOrNull(value) ?? 0)}%` }} />
    </div>
  );
}

function CardTitle({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="card-title-row">
      <span>{label}</span>
      <strong>{fmt(value, "limited")}</strong>
    </div>
  );
}

function ChecklistItem({ label, value, tone }: { label: string; value: unknown; tone: string }) {
  return (
    <div className={`check-item tone-${tone}`}>
      <span>{label}</span>
      <strong>{shortText(fmt(value, "Limited data"))}</strong>
    </div>
  );
}

function ListBlock({ title, items, empty }: { title: string; items?: unknown[]; empty: string }) {
  const values = (items ?? []).filter(Boolean).map(String);
  return (
    <div className="list-block">
      <strong>{title}</strong>
      {(values.length ? values : [empty]).map((item, index) => (
        <div className="list-item" key={`${title}-${index}`}>
          {item}
        </div>
      ))}
    </div>
  );
}

function LevelMarker({ label, value, low, high, tone }: { label: string; value?: number | null; low: number; high: number; tone: string }) {
  if (typeof value !== "number" || !Number.isFinite(value) || high <= low) {
    return null;
  }
  const top = clamp(100 - ((value - low) / (high - low)) * 100, 4, 96);
  return (
    <div className={`level-marker tone-${tone}`} style={{ top: `${top}%` }}>
      <span>{label}</span>
      <strong>{fmt(value)}</strong>
    </div>
  );
}

function SignalZone({ entry, stop, target, low, high }: { entry?: number | null; stop?: number | null; target?: number | null; low: number; high: number }) {
  if (typeof entry !== "number" || high <= low) {
    return null;
  }
  const values = [entry, stop, target].filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  if (values.length < 2) {
    return null;
  }
  const topRaw = 100 - ((Math.max(...values) - low) / (high - low)) * 100;
  const bottomRaw = 100 - ((Math.min(...values) - low) / (high - low)) * 100;
  const top = clamp(topRaw, 4, 96);
  const height = clamp(bottomRaw - topRaw, 10, 92);
  return (
    <div className="signal-zone" style={{ top: `${top}%`, height: `${height}%` }}>
      <span>Signal Zone</span>
    </div>
  );
}

function DeltaTile({ label, current, target }: { label: string; current?: number | null; target?: number | null }) {
  const delta = deltaFrom(current, target);
  return (
    <div className={`distance-tile tone-${delta.tone}`}>
      <span>{label}</span>
      <strong>{delta.text}</strong>
    </div>
  );
}

function fmt(value: unknown, fallback = "-"): string {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : fallback;
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return friendly(String(value));
}

function fmtContextValue(value: unknown): string {
  if (value === null || value === undefined) return "not_available";
  if (typeof value === "object") return JSON.stringify(value);
  return fmt(value, "not_available");
}

function friendly(value: string): string {
  const map: Record<string, string> = {
    not_available: "Currently unavailable",
    unavailable: "Currently unavailable",
    limited: "Limited data",
    partial: "Limited data",
    available: "Available",
    caution: "Caution",
    valid: "Valid",
    blocked: "Blocked",
    failed: "Failed",
    standby: "Standby",
    selective: "Selective execution",
    ready: "Ready",
    not_valid: "Not valid",
    synthetic_fallback: "Synthetic fallback",
    mock_fallback: "Mock fallback"
  };
  return map[value.toLowerCase()] ?? value;
}

function fmtDate(value?: string | null): string {
  if (!value) {
    return "no timestamp";
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function pctLabel(value: unknown, fallback: unknown = "not_available"): string {
  const number = numberOrNull(value);
  return number === null ? fmt(fallback) : `${Math.round(number)}%`;
}

function statusTone(value: unknown): string {
  const normalized = String(value ?? "").toLowerCase();
  if (["available", "valid", "ok", "fresh"].includes(normalized)) return "good";
  if (["caution", "partial", "limited", "warning", "stale_or_unknown"].includes(normalized)) return "warn";
  if (["blocked", "not_available", "unavailable", "failed"].includes(normalized)) return "bad";
  return "neutral";
}

function riskTone(value: unknown): string {
  const normalized = String(value ?? "").toLowerCase();
  if (["low", "valid", "pass", "passed", "ready"].includes(normalized)) return "good";
  if (["medium", "caution", "warning", "partial", "limited", "selective", "standby"].includes(normalized)) return "warn";
  if (["high", "extreme", "blocked", "failed", "not_available", "unavailable"].includes(normalized)) return "bad";
  return "neutral";
}

function signalTone(value: unknown): string {
  const text = String(value ?? "").toUpperCase();
  if (text.startsWith("BUY") || ["BULLISH", "POSITIVE"].includes(text)) return "good";
  if (text.startsWith("SELL") || ["BEARISH", "NEGATIVE"].includes(text)) return "bad";
  if (["WAIT", "NEUTRAL", "MIXED"].includes(text)) return "warn";
  return "neutral";
}

function numberOrNull(value: unknown): number | null {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function clamp(value: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, value));
}

function rangeFor(levels: number[]): { low: number; high: number } {
  if (!levels.length) {
    return { low: 0, high: 1 };
  }
  const low = Math.min(...levels);
  const high = Math.max(...levels);
  if (low === high) {
    const padding = Math.abs(high) * 0.01 || 1;
    return { low: low - padding, high: high + padding };
  }
  const padding = (high - low) * 0.12;
  return { low: low - padding, high: high + padding };
}

function deltaFrom(current?: number | null, target?: number | null): { tone: string; text: string } {
  if (typeof current !== "number" || typeof target !== "number" || !Number.isFinite(current) || !Number.isFinite(target)) {
    return { tone: "neutral", text: "baseline" };
  }
  const diff = current - target;
  const pct = target ? (diff / target) * 100 : 0;
  const tone = diff >= 0 ? "good" : "bad";
  const direction = diff >= 0 ? "up" : "down";
  return { tone, text: `${direction} ${Math.abs(diff).toLocaleString(undefined, { maximumFractionDigits: 2 })} / ${Math.abs(pct).toFixed(2)}%` };
}

function directionLabel(overview?: MarketOverview): string {
  const signal = String(overview?.signal ?? "").toUpperCase();
  const bias = String(overview?.bias ?? "").toUpperCase();
  if (signal.startsWith("BUY") || bias === "BULLISH") return "Upside map";
  if (signal.startsWith("SELL") || bias === "BEARISH") return "Downside map";
  return "Sideways map";
}

function directionArrow(overview?: MarketOverview): string {
  const label = directionLabel(overview);
  if (label.startsWith("Upside")) return "UP";
  if (label.startsWith("Downside")) return "DOWN";
  return "SIDE";
}

function executionMode(signal: SignalDecision | undefined, gate: RiskGate | undefined, dataMode: string): string {
  if (dataMode !== "live") {
    return "simulation_only";
  }
  const action = String(signal?.action ?? "").toUpperCase();
  const gateStatus = String(gate?.risk_status ?? "").toLowerCase();
  if (gateStatus === "blocked") return "blocked";
  if (["WAIT", "AVOID_HIGH_RISK"].includes(action)) return "standby";
  if (gateStatus === "caution" || signal?.warning_reason) return "selective";
  if (signal?.valid_signal === true) return "ready";
  return "limited";
}

function nextAction(mode: string, signal?: SignalDecision, gate?: RiskGate): string {
  if (mode === "blocked") return "Stand down until blockers clear.";
  if (mode === "standby") return "Wait for a cleaner trigger.";
  if (mode === "selective") return "Reduce size and require confirmation.";
  if (signal?.valid_signal === true && String(gate?.risk_status ?? "").toLowerCase() === "valid") return "Monitor entry zone.";
  return "Keep setup on watchlist.";
}

function invalidationText(signal?: SignalDecision, risk?: RiskPlan): string {
  const action = String(signal?.action ?? "").toUpperCase();
  if (typeof risk?.stop_loss === "number" && (action.startsWith("BUY") || action.startsWith("SELL"))) {
    return `Price breaches stop area ${fmt(risk.stop_loss)}`;
  }
  return signal?.blocked_reason ?? signal?.warning_reason ?? "Limited data";
}

function trendRead(overview?: MarketOverview): string {
  const bias = String(overview?.bias ?? "limited").toUpperCase();
  const confidence = numberOrNull(overview?.confidence);
  if (confidence === null) return `${bias} pressure`;
  if (confidence >= 70) return `${bias} pressure`;
  if (confidence >= 50) return `${bias} but selective`;
  return "Mixed pressure";
}

function trendNote(overview?: MarketOverview): string {
  const bias = String(overview?.bias ?? "").toUpperCase();
  const confidence = numberOrNull(overview?.confidence);
  if (confidence === null) return "Directional pressure is limited because confidence is not exposed.";
  if (["BULLISH", "BEARISH"].includes(bias) && confidence >= 70) return "Directional pressure is strong enough to prioritize aligned setups.";
  if (["BULLISH", "BEARISH"].includes(bias)) return "Directional pressure exists, but entries should wait for confirmation.";
  return "No dominant pressure; treat this as a range or wait environment.";
}

function momentumValue(signal?: SignalDecision): string {
  if (signal?.confirmation_reason) return "confirmation present";
  if (signal?.warning_reason) return "needs confirmation";
  return "Limited data";
}

function volatilityNote(value?: unknown): string {
  const text = String(value ?? "").toLowerCase();
  if (text.includes("high") || text.includes("volatile")) return "Tradable only with reduced size and wider invalidation.";
  if (text.includes("low")) return "Movement may be slow; avoid chasing weak breaks.";
  if (text && text !== "not_available") return "Volatility context is available for execution filtering.";
  return "Volatility context is currently unavailable.";
}

function dataHealth(quality?: DataQuality): string {
  const status = String(quality?.status ?? "not_available").toLowerCase();
  if (status === "available") return "Usable";
  if (["caution", "partial", "limited"].includes(status)) return "Use with caution";
  return "Limited data";
}

function scoreGrade(value: unknown): string {
  const score = numberOrNull(value);
  if (score === null) return "Limited data";
  if (score >= 80) return "A";
  if (score >= 65) return "B";
  if (score >= 50) return "C";
  return "D";
}

function readinessLabel(value: unknown): string {
  const score = numberOrNull(value);
  if (score === null) return "Limited data";
  if (score >= 75) return "Ready";
  if (score >= 55) return "Selective";
  return "Review";
}

function maxRiskLabel(value: unknown): string {
  const number = numberOrNull(value);
  return number === null ? "limited" : `${(number * 100).toFixed(2)}%`;
}

function rrProgress(value: unknown): number {
  const rr = numberOrNull(value);
  return rr === null ? 0 : clamp((rr / 3) * 100);
}

function validLabel(value: unknown): string {
  if (value === true) return "valid";
  if (value === false) return "not_valid";
  return "limited";
}

function confirmationNeeded(signal?: SignalDecision): string {
  return signal?.blocked_reason ?? signal?.warning_reason ?? signal?.confirmation_reason ?? "not_available";
}

function groupStatus(rows: EvidenceItem[]): string {
  const statuses = new Set(rows.map((row) => String(row.status ?? "not_available")));
  if (statuses.size === 1 && statuses.has("available")) return "available";
  if (statuses.has("caution") || statuses.has("not_available")) return "caution";
  return statuses.values().next().value ?? "not_available";
}

function emptyEvidenceCopy(title: string): string {
  if (title === "Contradictions") return "No contradiction is currently exposed for this analysis.";
  return "This evidence group is currently limited for this analysis.";
}

function componentLabel(value: string): string {
  const labels: Record<string, string> = {
    legacy_confidence: "Technical Confidence",
    signal_validation: "Signal Validation",
    data_quality: "Data Quality",
    risk_gate: "Risk Gate"
  };
  return labels[value] ?? labelize(value);
}

function labelize(value: string): string {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function resolveDataMode(result: CockpitAnalysisResult): string {
  const source = String(result.price_snapshot?.price_source ?? "").toLowerCase();
  const freshness = String(result.data_quality?.freshness_status ?? "").toLowerCase();
  const sentimentSource = String(result.sentiment_context?.source ?? "").toLowerCase();
  if (source.includes("mock") || source.includes("synthetic") || freshness.includes("mock") || sentimentSource.includes("mock")) {
    return "fallback";
  }
  return "live";
}

function resolveDeepSectionOrder(result: CockpitAnalysisResult): string[] {
  const defaultOrder = ["Evidence", "Heatmap", "Timeframes", "Regime", "Data", "Performance", "Sentiment", "Radar", "Context", "Validation"];
  const cockpitOrder = result.ui_sections?.order ?? [];
  const visibleMap = result.ui_sections?.visible ?? {};
  if (!cockpitOrder.length) {
    return defaultOrder;
  }

  const mapped = cockpitOrder
    .filter((section) => visibleMap[section] !== false)
    .map((section) => sectionTabLabel(section))
    .filter((tab): tab is string => Boolean(tab));
  const uniqueMapped = [...new Set(mapped)];
  const merged = [...uniqueMapped, ...defaultOrder.filter((tab) => !uniqueMapped.includes(tab))];
  return merged;
}

function buildDeepSectionMap(result: CockpitAnalysisResult): Record<string, JSX.Element> {
  return {
    Evidence: <EvidencePanel evidence={result.evidence_layer} />,
    Timeframes: <MtfPanel mtf={result.multi_timeframe} />,
    Regime: <RegimePanel regime={result.regime_analysis} structure={result.market_structure} />,
    Data: <DataQualityPanel quality={result.data_quality} />,
    Performance: <BacktestPanel snapshot={result.backtest_snapshot} />,
    Sentiment: <SentimentPanel sentiment={result.sentiment_context} />,
    Radar: <RadarDecisionPanel mtf={result.multi_timeframe} signal={result.signal_decision} gate={result.risk_gate} quality={result.data_quality} />,
    Context: <MarketContextPanel result={result} />,
    Validation: <ValidationPanel result={result} />,
    Heatmap: <HeatmapPanel confidence={result.confidence_breakdown} />
  };
}

function sectionTabLabel(section: string): string | null {
  const map: Record<string, string> = {
    evidence_layer: "Evidence",
    multi_timeframe: "Timeframes",
    regime_analysis: "Regime",
    data_quality: "Data",
    backtest_snapshot: "Performance",
    sentiment_context: "Sentiment",
    signal_decision: "Radar",
    market_context: "Context",
    validation_notes: "Validation",
    confidence_breakdown: "Heatmap",
    market_overview: "Evidence",
    market_structure: "Regime",
    risk_plan: "Radar",
    risk_gate: "Data",
    price_snapshot: "Context"
  };
  return map[section] ?? null;
}

function sectionRole(section: string): string {
  const roleMap: Record<string, string> = {
    price_snapshot: "Anchors latest tradable price and update timestamp",
    market_overview: "Summarizes directional state and trade quality",
    market_context: "Describes market environment and regime context",
    signal_decision: "Defines executable action and validation status",
    confidence_breakdown: "Explains confidence composition by component",
    evidence_layer: "Provides supporting and contradicting evidence",
    multi_timeframe: "Validates alignment across timeframes",
    regime_analysis: "Shows regime, volatility, and strategy fit",
    market_structure: "Maps structure levels and breakout/rejection logic",
    risk_plan: "Specifies entry, stop, target, and position risk",
    risk_gate: "Controls execution gating and risk constraints",
    data_quality: "Evaluates data freshness and integrity",
    sentiment_context: "Adds narrative/macro sentiment layer",
    backtest_snapshot: "Provides historical behavior snapshot",
    validation_notes: "Documents schema caveats and reliability notes"
  };
  return roleMap[section] ?? "Mapped section in cockpit contract";
}

function shortText(value: string): string {
  return value.length <= 120 ? value : `${value.slice(0, 117).trim()}...`;
}

function first(values?: string[]): string | null {
  return values?.find(Boolean) ?? null;
}
