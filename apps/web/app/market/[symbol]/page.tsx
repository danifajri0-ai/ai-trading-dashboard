import { CockpitConsole, PairTimeframeSelector } from "@/components/CockpitConsole";
import { getApiConfigState, getCockpitAnalysis, getSymbols } from "@/lib/api";

type MarketPageProps = {
  params: {
    symbol: string;
  };
  searchParams?: {
    timeframe?: string;
  };
};

export default async function MarketSymbolPage({ params, searchParams }: MarketPageProps) {
  let symbolsPayload = null;
  let symbolsError = "";
  try {
    symbolsPayload = await getSymbols();
  } catch (error) {
    const message = error instanceof Error ? error.message : "API response unavailable.";
    symbolsError = `Symbol catalog unavailable from backend. ${message}`;
  }
  const selectedSymbol = normalizeChoice(params.symbol, symbolsPayload?.symbols ?? [], "BTCUSD");
  const selectedTimeframe = normalizeChoice(searchParams?.timeframe, symbolsPayload?.timeframes ?? [], "H1");
  const apiConfigState = getApiConfigState();
  const apiStatus = apiConfigState === "local_default" ? "unconfigured" : "configured";
  let result = null;
  let loadError = "";
  if (symbolsPayload) {
    try {
      result = await getCockpitAnalysis(selectedSymbol, selectedTimeframe);
    } catch (error) {
      const message = error instanceof Error ? error.message : "API response unavailable.";
      loadError = `Cockpit data unavailable for ${selectedSymbol} ${selectedTimeframe}. ${message}`;
    }
  }

  return (
    <>
      {symbolsPayload ? (
        <PairTimeframeSelector
          symbolsPayload={symbolsPayload}
          selectedSymbol={selectedSymbol}
          selectedTimeframe={selectedTimeframe}
        />
      ) : (
        <section className="card">
          <h2>Symbol Catalog Unavailable</h2>
          <p className="section-subtitle">
            Frontend strict mode aktif. Pair/timeframe selector hanya boleh dari backend API.
          </p>
          <p className="section-subtitle">{symbolsError || "Please verify API deployment and CORS settings."}</p>
        </section>
      )}
      {symbolsPayload && result ? (
        <CockpitConsole result={result} apiStatus={apiStatus} />
      ) : symbolsPayload ? (
        <section className="card">
          <h2>Live Cockpit Unavailable</h2>
          <p className="section-subtitle">
            Data analisa live tidak bisa dimuat. Frontend tidak memakai mock agar parity data Streamlit ke Next.js tetap akurat.
          </p>
          <p className="section-subtitle">{loadError || "Please verify API deployment and CORS settings."}</p>
        </section>
      ) : null}
    </>
  );
}

function normalizeChoice(value: string | undefined, allowed: string[], fallback: string): string {
  const normalized = String(value || fallback).trim().toUpperCase();
  return allowed.includes(normalized) ? normalized : fallback;
}
