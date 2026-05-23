from __future__ import annotations

from typing import Literal


FeatureTier = Literal["free", "pro", "premium", "experimental"]


FEATURE_FLAGS: dict[str, set[FeatureTier]] = {
    "legacy_dashboard": {"free", "pro", "premium", "experimental"},
    "rich_cockpit_v2": {"free", "pro", "premium", "experimental"},
    "evidence_layer": {"free", "pro", "premium", "experimental"},
    "multi_timeframe_analysis": {"pro", "premium", "experimental"},
    "regime_scoring": {"pro", "premium", "experimental"},
    "backtest_snapshot": {"premium", "experimental"},
    "signal_performance_memory": {"premium", "experimental"},
    "external_news_provider": {"premium", "experimental"},
    "local_llm_reasoning": {"experimental"},
    "api_llm_reasoning": {"experimental"},
}


TIER_ORDER: tuple[FeatureTier, ...] = ("free", "pro", "premium", "experimental")


def normalize_tier(tier: str | None) -> FeatureTier:
    normalized = str(tier or "free").strip().lower()
    if normalized in TIER_ORDER:
        return normalized  # type: ignore[return-value]
    return "free"
