import type { AnalysisHistoryItem, AnalysisResult, CockpitAnalysisResult, SymbolsPayload, WatchlistItem } from "@/lib/types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export type ApiConfigState = "configured" | "auto_vercel" | "local_default";
export type ApiRequestOptions = {
  baseUrl?: string;
  headers?: HeadersInit;
};

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

function normalizeBaseUrl(value: string): string {
  return value.replace(/\/+$/, "");
}

function getVercelApiBaseUrl(): string | null {
  const host = process.env.VERCEL_URL?.trim();
  if (!host) {
    return null;
  }
  const normalizedHost = host.replace(/^https?:\/\//i, "").replace(/\/+$/, "");
  if (!normalizedHost) {
    return null;
  }
  return `https://${normalizedHost}/backend`;
}

export function buildServerApiRequestOptions(requestHeaders: Headers): ApiRequestOptions {
  const requestHost = requestHeaders.get("x-forwarded-host") || requestHeaders.get("host");
  const requestProto = requestHeaders.get("x-forwarded-proto") || "https";
  const forwardedHeaders: Record<string, string> = {};
  const cookieHeader = requestHeaders.get("cookie");
  const authorizationHeader = requestHeaders.get("authorization");
  const bypassHeader = requestHeaders.get("x-vercel-protection-bypass");
  const setBypassCookieHeader = requestHeaders.get("x-vercel-set-bypass-cookie");

  if (cookieHeader) {
    forwardedHeaders.cookie = cookieHeader;
  }
  if (authorizationHeader) {
    forwardedHeaders.authorization = authorizationHeader;
  }
  if (bypassHeader) {
    forwardedHeaders["x-vercel-protection-bypass"] = bypassHeader;
  }
  if (setBypassCookieHeader) {
    forwardedHeaders["x-vercel-set-bypass-cookie"] = setBypassCookieHeader;
  }

  return {
    baseUrl: requestHost ? `${requestProto}://${requestHost}/backend` : undefined,
    headers: forwardedHeaders
  };
}

export function getApiConfigState(): ApiConfigState {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (configured && /^https?:\/\//i.test(configured)) {
    return "configured";
  }
  if (getVercelApiBaseUrl()) {
    return "auto_vercel";
  }
  return "local_default";
}

export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (configured && /^https?:\/\//i.test(configured)) {
    return normalizeBaseUrl(configured);
  }
  const vercelBaseUrl = getVercelApiBaseUrl();
  if (vercelBaseUrl) {
    return vercelBaseUrl;
  }
  return DEFAULT_API_BASE_URL;
}

function resolveApiBaseUrl(options?: ApiRequestOptions | string): string {
  const overrideBaseUrl = typeof options === "string" ? options : options?.baseUrl;
  if (overrideBaseUrl && /^https?:\/\//i.test(overrideBaseUrl)) {
    return normalizeBaseUrl(overrideBaseUrl);
  }
  return getApiBaseUrl();
}

function resolveForwardedHeaders(options?: ApiRequestOptions | string): HeadersInit | undefined {
  if (!options || typeof options === "string") {
    return undefined;
  }
  return options.headers;
}

async function fetchJson<T>(path: string, init?: RequestInit, options?: ApiRequestOptions | string): Promise<T> {
  const url = `${resolveApiBaseUrl(options)}${path}`;
  const forwardedHeaders = resolveForwardedHeaders(options);
  try {
    const response = await fetch(url, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(forwardedHeaders || {}),
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

type LegacyAnalysisPayload = {
  ticker: string;
  current_price: number;
  indicators?: {
    rsi?: number;
    macd?: number;
    macd_signal?: number;
    macd_hist?: number;
    sma_20?: number;
    ema_20?: number;
  };
  ai_recommendation?: {
    action?: string;
    reasoning?: string;
  };
  historical_data?: Array<{
    date?: number;
    open?: number;
    high?: number;
    low?: number;
    close?: number;
    sma?: number;
    ema?: number;
  }>;
};

function toLegacyTicker(symbol: string): string {
  const clean = symbol.trim().toUpperCase();
  if (clean.includes("-") || clean.includes("=")) {
    return clean;
  }
  if (clean.endsWith("USD") && clean.length > 3) {
    return `${clean.slice(0, -3)}-USD`;
  }
  return clean;
}

function inferBiasAndConfidence(payload: LegacyAnalysisPayload): { bias: string; confidence: number } {
  const close = payload.current_price;
  const sma = payload.indicators?.sma_20;
  const rsi = payload.indicators?.rsi;
  const action = (payload.ai_recommendation?.action || "").toUpperCase();

  let bias = "NEUTRAL";
  if (typeof sma === "number") {
    bias = close >= sma ? "BULLISH" : "BEARISH";
  } else if (action === "BUY") {
    bias = "BULLISH";
  } else if (action === "SELL") {
    bias = "BEARISH";
  }

  let confidence = 62;
  if (typeof rsi === "number") {
    const rsiDistance = Math.min(Math.abs(rsi - 50), 35);
    confidence = Math.round(60 + rsiDistance);
  }
  confidence = Math.max(50, Math.min(95, confidence));
  return { bias, confidence };
}

function mapLegacyToCockpit(payload: LegacyAnalysisPayload, timeframe: string): CockpitAnalysisResult {
  const { bias, confidence } = inferBiasAndConfidence(payload);
  const action = (payload.ai_recommendation?.action || "HOLD").toUpperCase();
  const rsi = payload.indicators?.rsi ?? null;
  const reasoning = payload.ai_recommendation?.reasoning || "Legacy backend recommendation.";
  const latestBar = payload.historical_data?.[payload.historical_data.length - 1];
  const entry = latestBar?.close ?? payload.current_price;
  const minMove = Math.max(Math.abs(entry) * 0.0025, 0.0001);
  let stop = typeof latestBar?.low === "number" ? latestBar.low : entry - minMove;
  let target = typeof latestBar?.high === "number" ? latestBar.high : entry + minMove * 1.5;
  if (action === "SELL") {
    stop = typeof latestBar?.high === "number" ? latestBar.high : entry + minMove;
    target = typeof latestBar?.low === "number" ? latestBar.low : entry - minMove * 1.5;
    if (stop <= entry) stop = entry + minMove;
    if (target >= entry) target = entry - minMove * 1.5;
  } else {
    if (stop >= entry) stop = entry - minMove;
    if (target <= entry) target = entry + minMove * 1.5;
  }
  const rr = Math.round((Math.abs(target - entry) / Math.max(Math.abs(entry - stop), 0.0001)) * 100) / 100;

  return {
    schema_version: "cockpit.v1-legacy-adapter",
    symbol: payload.ticker,
    timeframe,
    price_snapshot: {
      status: "available",
      symbol: payload.ticker,
      timeframe,
      last_price: payload.current_price,
      bid: null,
      ask: null,
      price_source: "legacy_backend",
      updated_at: new Date().toISOString(),
      notes: ["Mapped from legacy /api/analysis endpoint"]
    },
    market_overview: {
      status: "available",
      bias,
      signal: action,
      risk_level: "medium",
      confidence,
      trade_quality_score: confidence,
      summary: reasoning,
      warnings: []
    },
    market_context: {
      status: "available",
      context: {
        rsi,
        macd: payload.indicators?.macd ?? null,
        sma_20: payload.indicators?.sma_20 ?? null,
        ema_20: payload.indicators?.ema_20 ?? null
      },
      notes: ["Legacy context fields adapted for cockpit rendering"]
    },
    signal_decision: {
      status: "available",
      action,
      confidence,
      bias,
      validation_score: confidence,
      valid_signal: action !== "HOLD",
      blocked_reason: null,
      warning_reason: null,
      confirmation_reason: reasoning,
      reasons: [reasoning],
      notes: []
    },
    confidence_breakdown: {
      status: "available",
      overall_score: confidence,
      components: {
        rsi_component: { score: rsi ?? 50, weight: 0.5, weighted_score: (rsi ?? 50) * 0.5 },
        trend_component: { score: confidence, weight: 0.5, weighted_score: confidence * 0.5 }
      },
      notes: ["Confidence synthesized from legacy indicator payload"]
    },
    evidence_layer: {
      status: "available",
      reasons: [reasoning],
      warnings: [],
      technical_notes: [`RSI: ${rsi ?? "n/a"}`, `MACD: ${payload.indicators?.macd ?? "n/a"}`],
      sentiment_notes: [],
      technical_evidence: [{ label: "Legacy indicators", status: "available", detail: "RSI/MACD/SMA/EMA available", score: confidence }],
      risk_evidence: [{ label: "Risk snapshot", status: "caution", detail: "Derived risk plan from latest bar", score: 60 }],
      data_quality_evidence: [{ label: "Adapter mode", status: "caution", detail: "Using compatibility mapping from legacy backend", score: 70 }],
      contradictions: []
    },
    multi_timeframe: {
      status: "partial",
      primary_timeframe: timeframe,
      alignment_score: confidence,
      dominant_bias: bias,
      per_timeframe_bias: { [timeframe]: bias },
      conflict_notes: [],
      entry_timing: action === "BUY" ? "momentum_follow" : action === "SELL" ? "reversal_watch" : "wait",
      timeframes: { [timeframe]: { bias, signal: action } },
      notes: ["Legacy backend does not expose native multi-timeframe grid"]
    },
    regime_analysis: {
      status: "partial",
      regime: bias === "BULLISH" ? "trend_up" : bias === "BEARISH" ? "trend_down" : "sideways",
      regime_score: confidence,
      volatility_state: "normal",
      liquidity_condition: "unknown",
      preferred_strategy: action === "HOLD" ? "wait" : "trend_follow",
      risk_adjustment: "standard",
      notes: ["Regime inferred from adapted fields"]
    },
    market_structure: {
      status: "partial",
      structure: bias,
      support: typeof latestBar?.low === "number" ? latestBar.low : null,
      resistance: typeof latestBar?.high === "number" ? latestBar.high : null,
      support_distance_pct: null,
      resistance_distance_pct: null,
      breakout_note: null,
      rejection_note: null,
      notes: ["Support/resistance approximated from latest historical candle"]
    },
    risk_plan: {
      status: "available",
      risk_level: "medium",
      entry_area: entry,
      stop_loss: stop,
      take_profit: target,
      risk_reward: rr,
      max_risk_pct: 0.02,
      notes: ["Risk plan adapted from legacy candle snapshot"]
    },
    risk_gate: {
      status: action === "HOLD" ? "caution" : "available",
      risk_status: action === "HOLD" ? "wait" : "valid",
      reasons: [reasoning],
      raw: {}
    },
    data_quality: {
      status: "caution",
      score: 70,
      freshness_status: "unknown",
      issues: ["Legacy backend contract mapped through compatibility adapter"],
      raw: {}
    },
    sentiment_context: {
      status: "not_available",
      sentiment_label: null,
      sentiment_score: null,
      context: [],
      source: null,
      notes: ["Legacy backend has no sentiment context endpoint"]
    },
    backtest_snapshot: {
      status: "not_available",
      metrics: {},
      notes: ["Backtest not provided by legacy backend contract"]
    },
    validation_notes: {
      status: "caution",
      notes: ["Cockpit rendered using legacy compatibility adapter"]
    },
    ui_sections: {
      status: "available",
      order: [],
      visible: {}
    },
    feature_flags: {
      compatibility_mode: true,
      source: "legacy_backend"
    },
    legacy_result: {
      symbol: payload.ticker,
      timeframe,
      bias,
      signal: action,
      confidence,
      risk_level: "medium",
      trade_quality_score: confidence,
      reasons: [reasoning],
      warnings: [],
      technical_summary: {
        trend: bias,
        rsi: rsi ?? undefined,
        notes: ["Adapted from /api/analysis indicators"]
      }
    }
  };
}

export async function getAnalysis(
  symbol = "BTCUSD",
  timeframe = "H1",
  options?: ApiRequestOptions | string
): Promise<AnalysisResult> {
  try {
    return await fetchJson<AnalysisResult>("/analyze", {
      method: "POST",
      body: JSON.stringify({ symbol, timeframe })
    }, options);
  } catch {
    const legacy = await fetchJson<LegacyAnalysisPayload>(
      `/api/analysis/${encodeURIComponent(toLegacyTicker(symbol))}`,
      undefined,
      options
    );
    const mapped = mapLegacyToCockpit(legacy, timeframe);
    return mapped.legacy_result as AnalysisResult;
  }
}

export async function getCockpitAnalysis(
  symbol = "BTCUSD",
  timeframe = "H1",
  options?: ApiRequestOptions | string
): Promise<CockpitAnalysisResult> {
  try {
    return await fetchJson<CockpitAnalysisResult>("/cockpit/analyze", {
      method: "POST",
      body: JSON.stringify({ symbol, timeframe })
    }, options);
  } catch {
    const legacy = await fetchJson<LegacyAnalysisPayload>(
      `/api/analysis/${encodeURIComponent(toLegacyTicker(symbol))}`,
      undefined,
      options
    );
    return mapLegacyToCockpit(legacy, timeframe);
  }
}

export async function getSymbols(options?: ApiRequestOptions | string): Promise<SymbolsPayload> {
  try {
    const payload = await fetchJson<SymbolsPayload>("/symbols", undefined, options);
    if (!Array.isArray(payload.symbols) || !Array.isArray(payload.timeframes)) {
      throw new ApiUnavailableError("/symbols", "API symbols payload is invalid.");
    }
    return payload;
  } catch {
    const queries = ["BTC", "ETH", "AAPL", "TSLA", "EUR", "XAU"];
    const symbols = new Set<string>();
    for (const q of queries) {
      try {
        const items = await fetchJson<Array<{ symbol?: string }>>(
          `/api/portfolio/search?q=${encodeURIComponent(q)}`,
          undefined,
          options
        );
        for (const item of items) {
          if (item?.symbol) {
            symbols.add(String(item.symbol).toUpperCase());
          }
        }
      } catch {
        // continue probing other queries
      }
    }
    if (!symbols.size) {
      throw new ApiUnavailableError("/api/portfolio/search", "Legacy backend symbol discovery failed.");
    }
    return {
      symbols: Array.from(symbols).sort((a, b) => a.localeCompare(b)),
      timeframes: ["H1"]
    };
  }
}

export async function getHistory(limit = 50, options?: ApiRequestOptions | string): Promise<AnalysisHistoryItem[]> {
  try {
    const payload = await fetchJson<{ items: AnalysisHistoryItem[] }>(
      `/api/analysis/history?limit=${limit}`,
      undefined,
      options
    );
    return payload.items ?? [];
  } catch {
    return [];
  }
}

export async function getWatchlist(limit = 100, options?: ApiRequestOptions | string): Promise<WatchlistItem[]> {
  try {
    const payload = await fetchJson<{ items: WatchlistItem[] }>(
      `/api/watchlist?limit=${limit}`,
      undefined,
      options
    );
    return payload.items ?? [];
  } catch {
    return [];
  }
}
