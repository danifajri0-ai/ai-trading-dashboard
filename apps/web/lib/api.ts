import type { AnalysisHistoryItem, AnalysisResult, WatchlistItem } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
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
      throw new Error(`API request failed: ${response.status}`);
    }
    return (await response.json()) as T;
  } catch {
    throw new Error("API_UNAVAILABLE");
  }
}

export async function getAnalysis(symbol = "BTCUSD", timeframe = "H1"): Promise<AnalysisResult> {
  try {
    return await fetchJson<AnalysisResult>("/analyze", {
      method: "POST",
      body: JSON.stringify({ symbol, timeframe })
    });
  } catch {
    return mockAnalysis(symbol, timeframe);
  }
}

export async function getHistory(limit = 50): Promise<AnalysisHistoryItem[]> {
  try {
    const payload = await fetchJson<{ items: AnalysisHistoryItem[] }>(`/api/analysis/history?limit=${limit}`);
    return payload.items ?? [];
  } catch {
    return mockHistory();
  }
}

export async function getWatchlist(limit = 100): Promise<WatchlistItem[]> {
  try {
    const payload = await fetchJson<{ items: WatchlistItem[] }>(`/api/watchlist?limit=${limit}`);
    return payload.items ?? [];
  } catch {
    return mockWatchlist();
  }
}

function mockAnalysis(symbol: string, timeframe: string): AnalysisResult {
  return {
    symbol,
    timeframe,
    bias: "BULLISH",
    signal: "BUY",
    confidence: 72,
    risk_level: "medium",
    trade_quality_score: 66,
    reasons: [
      "EMA trend alignment supports upside continuation.",
      "Momentum remains stable with controlled volatility."
    ],
    warnings: ["Monitor macro news around high-impact sessions."],
    technical_summary: {
      trend: "Bullish continuation",
      ema_fast: 65210,
      ema_slow: 64780,
      rsi: 58.3,
      atr: 412.5,
      support: 64500,
      resistance: 66150,
      notes: ["Volume slightly above 40-candle average."]
    },
    sentiment_summary: {
      sentiment_label: "Positive",
      sentiment_score: 63,
      context: ["Risk appetite improving in US session."],
      source: "mock_fallback"
    },
    risk_summary: {
      risk_level: "medium",
      entry_area: 65120,
      stop_loss: 64620,
      take_profit: 66080,
      risk_reward: 1.92,
      max_risk_pct: 0.02,
      notes: ["Use reduced size if volatility spikes."]
    },
    market_context_lite: {
      regime_label: "trend_continuation",
      volatility_state: "normal_volatility",
      trend_state: "bullish_trend"
    },
    signal_explanation_lite: {
      explanation_summary: "Trend and momentum are aligned for selective long setups."
    }
  };
}

function mockHistory(): AnalysisHistoryItem[] {
  return [
    {
      id: "mock-1",
      symbol: "BTCUSD",
      timeframe: "H1",
      signal: "BUY",
      bias: "BULLISH",
      confidence: 72,
      summary: "Trend continuation setup",
      created_at: new Date().toISOString()
    },
    {
      id: "mock-2",
      symbol: "XAUUSD",
      timeframe: "H4",
      signal: "WAIT",
      bias: "NEUTRAL",
      confidence: 49,
      summary: "Range condition, waiting breakout confirmation",
      created_at: new Date(Date.now() - 3600000).toISOString()
    }
  ];
}

function mockWatchlist(): WatchlistItem[] {
  return [
    {
      id: "mock-w1",
      symbol: "BTCUSD",
      market_type: "crypto",
      notes: "Primary momentum pair",
      created_at: new Date().toISOString()
    },
    {
      id: "mock-w2",
      symbol: "XAUUSD",
      market_type: "commodity",
      notes: "Macro-sensitive hedge instrument",
      created_at: new Date(Date.now() - 7200000).toISOString()
    }
  ];
}
