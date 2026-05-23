from __future__ import annotations

from config import FEATURE_FLAGS, normalize_tier


def is_feature_enabled(feature_name: str, tier: str | None = "free") -> bool:
    normalized_feature = str(feature_name or "").strip()
    normalized_tier = normalize_tier(tier)
    enabled_tiers = FEATURE_FLAGS.get(normalized_feature)
    if not enabled_tiers:
        return False
    return normalized_tier in enabled_tiers


def enabled_features_for_tier(tier: str | None = "free") -> list[str]:
    normalized_tier = normalize_tier(tier)
    return sorted(
        feature
        for feature, tiers in FEATURE_FLAGS.items()
        if normalized_tier in tiers
    )
