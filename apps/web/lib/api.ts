import type { AnalysisHistoryItem, AnalysisResult, CockpitAnalysisResult, SymbolsPayload, WatchlistItem } from "@/lib/types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export class ApiUnavailableError extends Error {
  code: string;
  path: string;
  status?: number;

  constructor(path: string, message: string, status?: number) {
    super(message);
    this.name = "ApiUnavailableError";
    this.code = "API_UNAVAILABLE";
    this.path = path;
    this.status = status;
  }
}

function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (!configured) {
    return DEFAULT_API_BASE_URL;
  }
  if (!/^https?:\/\//i.test(configured)) {
    return DEFAULT_API_BASE_URL;
  }
  return configured.replace(/\/+$/, "");
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`;
  try {
    const response = await fetch(url, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {})
      },
      cache: "no-store"
    });
    if (!response.ok) {
      throw new ApiUnavailableError(path, `API request failed: ${response.status}`, response.status);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiUnavailableError) {
      throw error;
    }
    throw new ApiUnavailableError(path, "API request could not be completed.");
  }
}

export async function getAnalysis(symbol = "BTCUSD", timeframe = "H1"): Promise<AnalysisResult> {
  return fetchJson<AnalysisResult>("/analyze", {
    method: "POST",
    body: JSON.stringify({ symbol, timeframe })
  });
}

export async function getCockpitAnalysis(symbol = "BTCUSD", timeframe = "H1"): Promise<CockpitAnalysisResult> {
  return fetchJson<CockpitAnalysisResult>("/cockpit/analyze", {
    method: "POST",
    body: JSON.stringify({ symbol, timeframe })
  });
}

export async function getSymbols(): Promise<SymbolsPayload> {
  const payload = await fetchJson<SymbolsPayload>("/symbols");
  if (!Array.isArray(payload.symbols) || !Array.isArray(payload.timeframes)) {
    throw new ApiUnavailableError("/symbols", "API symbols payload is invalid.");
  }
  return payload;
}

export async function getHistory(limit = 50): Promise<AnalysisHistoryItem[]> {
  try {
    const payload = await fetchJson<{ items: AnalysisHistoryItem[] }>(`/api/analysis/history?limit=${limit}`);
    return payload.items ?? [];
  } catch {
    return [];
  }
}

export async function getWatchlist(limit = 100): Promise<WatchlistItem[]> {
  try {
    const payload = await fetchJson<{ items: WatchlistItem[] }>(`/api/watchlist?limit=${limit}`);
    return payload.items ?? [];
  } catch {
    return [];
  }
}
