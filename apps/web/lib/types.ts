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

export type SymbolsPayload = {
  symbols: string[];
  timeframes: string[];
  categories?: Record<string, string[]>;
};

export type StatusValue = "available" | "partial" | "caution" | "not_available" | string;

export type PriceSnapshot = {
  status?: StatusValue;
  symbol?: string;
  timeframe?: string;
  last_price?: number | null;
  bid?: number | null;
  ask?: number | null;
  price_source?: string | null;
  updated_at?: string | null;
  notes?: string[];
};

export type MarketOverview = {
  status?: StatusValue;
  bias?: string;
  signal?: string;
  risk_level?: string;
  confidence?: number;
  trade_quality_score?: number;
  summary?: string;
  warnings?: string[];
};

export type SignalDecision = {
  status?: StatusValue;
  action?: string;
  confidence?: number;
  bias?: string;
  validation_score?: number | null;
  valid_signal?: boolean | null;
  blocked_reason?: string | null;
  warning_reason?: string | null;
  confirmation_reason?: string | null;
  reasons?: string[];
  notes?: string[];
};

export type RiskPlan = {
  status?: StatusValue;
  risk_level?: string;
  entry_area?: number | null;
  stop_loss?: number | null;
  take_profit?: number | null;
  risk_reward?: number | null;
  max_risk_pct?: number | null;
  notes?: string[];
};

export type RiskGate = {
  status?: StatusValue;
  risk_status?: string | null;
  reasons?: string[];
  raw?: Record<string, unknown>;
};

export type ConfidenceBreakdown = {
  status?: StatusValue;
  overall_score?: number;
  components?: Record<string, { score?: number; weight?: number; weighted_score?: number } | Record<string, unknown>>;
  notes?: string[];
};

export type EvidenceLayer = {
  status?: StatusValue;
  reasons?: string[];
  warnings?: string[];
  technical_notes?: string[];
  sentiment_notes?: string[];
  technical_evidence?: EvidenceItem[];
  risk_evidence?: EvidenceItem[];
  data_quality_evidence?: EvidenceItem[];
  contradictions?: EvidenceItem[];
};

export type EvidenceItem = {
  label?: string;
  status?: StatusValue;
  detail?: string;
  score?: number | null;
};

export type MultiTimeframe = {
  status?: StatusValue;
  primary_timeframe?: string;
  alignment_score?: number | null;
  dominant_bias?: string | null;
  per_timeframe_bias?: Record<string, string>;
  conflict_notes?: string[];
  entry_timing?: string | null;
  timeframes?: Record<string, Record<string, unknown>>;
  notes?: string[];
};

export type RegimeAnalysis = {
  status?: StatusValue;
  regime?: string | null;
  regime_score?: number | null;
  volatility_state?: string | null;
  liquidity_condition?: string | null;
  preferred_strategy?: string | null;
  risk_adjustment?: string | null;
  notes?: string[];
};

export type MarketStructure = {
  status?: StatusValue;
  structure?: string | null;
  support?: number | null;
  resistance?: number | null;
  support_distance_pct?: number | null;
  resistance_distance_pct?: number | null;
  breakout_note?: string | null;
  rejection_note?: string | null;
  notes?: string[];
};

export type DataQuality = {
  status?: StatusValue;
  score?: number | null;
  freshness_status?: string | null;
  issues?: string[];
  raw?: Record<string, unknown>;
};

export type SentimentContext = {
  status?: StatusValue;
  sentiment_label?: string | null;
  sentiment_score?: number | null;
  context?: string[];
  source?: string | null;
  notes?: string[];
};

export type BacktestSnapshot = {
  status?: StatusValue;
  metrics?: Record<string, Record<string, unknown>>;
  notes?: string[];
};

export type CockpitAnalysisResult = {
  schema_version?: string;
  symbol: string;
  timeframe: string;
  price_snapshot?: PriceSnapshot;
  market_overview?: MarketOverview;
  market_context?: { status?: StatusValue; context?: Record<string, unknown>; notes?: string[] };
  signal_decision?: SignalDecision;
  confidence_breakdown?: ConfidenceBreakdown;
  evidence_layer?: EvidenceLayer;
  multi_timeframe?: MultiTimeframe;
  regime_analysis?: RegimeAnalysis;
  market_structure?: MarketStructure;
  risk_plan?: RiskPlan;
  risk_gate?: RiskGate;
  data_quality?: DataQuality;
  sentiment_context?: SentimentContext;
  backtest_snapshot?: BacktestSnapshot;
  validation_notes?: { status?: StatusValue; notes?: string[] };
  ui_sections?: { status?: StatusValue; order?: string[]; visible?: Record<string, boolean> };
  feature_flags?: Record<string, unknown>;
  legacy_result?: AnalysisResult;
};
