export type AnalysisResult = {
  symbol: string;
  timeframe: string;
  bias: string;
  signal: string;
  confidence: number;
  risk_level: string;
  trade_quality_score: number;
  reasons: string[];
  warnings: string[];
  technical_summary?: {
    trend?: string;
    ema_fast?: number;
    ema_slow?: number;
    rsi?: number;
    atr?: number;
    support?: number;
    resistance?: number;
    notes?: string[];
  };
  sentiment_summary?: {
    sentiment_label?: string;
    sentiment_score?: number;
    context?: string[];
    source?: string;
  };
  risk_summary?: {
    risk_level?: string;
    entry_area?: number | null;
    stop_loss?: number | null;
    take_profit?: number | null;
    risk_reward?: number | null;
    max_risk_pct?: number | null;
    notes?: string[];
  };
  market_context_lite?: Record<string, unknown> | null;
  signal_explanation_lite?: Record<string, unknown> | null;
};

export type AnalysisHistoryItem = {
  id?: string;
  symbol: string;
  timeframe: string;
  signal: string;
  bias: string;
  confidence: number;
  summary: string;
  created_at: string;
};

export type WatchlistItem = {
  id?: string;
  symbol: string;
  market_type: string;
  notes: string;
  created_at: string;
};
