import { headers } from "next/headers";

import { CockpitConsole, PairTimeframeSelector } from "@/components/CockpitConsole";
import {
  buildServerApiRequestOptions,
  DEFAULT_SUPPORTED_SYMBOLS,
  DEFAULT_SUPPORTED_TIMEFRAMES,
  getApiConfigState,
  getCockpitAnalysis,
  getSymbols
} from "@/lib/api";

type DashboardPageProps = {
  searchParams?: {
    symbol?: string;
    timeframe?: string;
  };
};

export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const requestHeaders = headers();
  const apiRequestOptions = buildServerApiRequestOptions(requestHeaders);
  const requestedSymbol = normalizeChoice(searchParams?.symbol, Array.from(DEFAULT_SUPPORTED_SYMBOLS), "BTCUSD");
  const requestedTimeframe = normalizeChoice(
    searchParams?.timeframe,
    Array.from(DEFAULT_SUPPORTED_TIMEFRAMES),
    "H1"
  );

  const symbolsPromise = getSymbols(apiRequestOptions);
  const analysisPromise = getCockpitAnalysis(requestedSymbol, requestedTimeframe, apiRequestOptions);

  let symbolsPayload = null;
  let symbolsError = "";
  let result = null;
  let loadError = "";
  const [symbolsOutcome, analysisOutcome] = await Promise.allSettled([symbolsPromise, analysisPromise]);

  if (symbolsOutcome.status === "fulfilled") {
    symbolsPayload = symbolsOutcome.value;
  } else {
    const message = symbolsOutcome.reason instanceof Error ? symbolsOutcome.reason.message : "API response unavailable.";
    symbolsError = `Symbol catalog unavailable from backend. ${message}`;
  }

  if (analysisOutcome.status === "fulfilled") {
    result = analysisOutcome.value;
  } else {
    const message = analysisOutcome.reason instanceof Error ? analysisOutcome.reason.message : "API response unavailable.";
    loadError = `Cockpit data unavailable for ${requestedSymbol} ${requestedTimeframe}. ${message}`;
  }

  const selectedSymbol = normalizeChoice(searchParams?.symbol, symbolsPayload?.symbols ?? [], requestedSymbol);
  const selectedTimeframe = normalizeChoice(searchParams?.timeframe, symbolsPayload?.timeframes ?? [], requestedTimeframe);
  const apiConfigState = getApiConfigState();
  const apiStatus = apiConfigState === "local_default" ? "unconfigured" : "configured";

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
      {result ? (
        <CockpitConsole result={result} apiStatus={apiStatus} />
      ) : (
        <section className="card">
          <h2>Live Cockpit Unavailable</h2>
          <p className="section-subtitle">
            Data analisa live tidak bisa dimuat. Frontend tidak memakai mock agar parity data Streamlit ke Next.js tetap akurat.
          </p>
          <p className="section-subtitle">{loadError || "Please verify API deployment and CORS settings."}</p>
        </section>
      )}
    </>
  );
}

function normalizeChoice(value: string | undefined, allowed: string[], fallback: string): string {
  const normalized = String(value || fallback).trim().toUpperCase();
  return allowed.includes(normalized) ? normalized : fallback;
}
