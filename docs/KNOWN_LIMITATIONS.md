# Known Limitations

Rich AI Trading Cockpit v1 is a defensive decision-support layer. It is not a promise of profit and must not be treated as financial advice.

## Data and Provider Limits

- Market data can be stale, missing, delayed, or unavailable depending on provider behavior.
- News and sentiment providers are optional. If no provider is configured, sentiment should return `not_available` or `limited`.
- Local/dev mode must work without paid API keys.
- Multi-timeframe sections may be partial when one or more timeframe fetches fail.

## Signal and Evidence Limits

- Evidence scoring is rule-based and lightweight.
- Signal validation can reduce confidence, but it cannot guarantee trade outcomes.
- Contradictions and warnings should be reviewed manually before acting.
- Confidence is a decision-support score, not a probability of profit.

## Backtesting and Memory Limits

- Backtest snapshot is lightweight and early-stage.
- Historical signal memory depends on locally recorded snapshots and may have small sample sizes.
- Estimated win rate, drawdown, and risk/reward are not guarantees.
- Missing or insufficient data should return `not_available`, not fabricated metrics.

## LLM Limits

- LLM reasoning is disabled by default.
- Local and API modes require explicit client wiring before use.
- Template reasoning is deterministic and only explains existing schema fields.
- LLM output, when enabled later, must not create unsupported market facts.

## UI and Deployment Limits

- Streamlit UI should render schema fields only and avoid recalculating indicators.
- Legacy compatibility remains in place; cleanup is intentionally deferred.
- Streamlit Cloud must run `apps/streamlit_app/app.py`.
- Root `app.py` remains a legacy compatibility entrypoint and should not be removed in v1.

