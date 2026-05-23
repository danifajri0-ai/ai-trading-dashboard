from __future__ import annotations

from services.feature_gate_service import enabled_features_for_tier, is_feature_enabled


def test_feature_gate_keeps_core_cockpit_available_for_free_tier() -> None:
    assert is_feature_enabled("legacy_dashboard", "free") is True
    assert is_feature_enabled("rich_cockpit_v2", "free") is True
    assert is_feature_enabled("evidence_layer", "free") is True


def test_feature_gate_blocks_future_premium_features_for_free_tier() -> None:
    assert is_feature_enabled("backtest_snapshot", "free") is False
    assert is_feature_enabled("signal_performance_memory", "free") is False
    assert is_feature_enabled("local_llm_reasoning", "free") is False


def test_feature_gate_allows_expected_tiers() -> None:
    assert is_feature_enabled("multi_timeframe_analysis", "pro") is True
    assert is_feature_enabled("backtest_snapshot", "premium") is True
    assert is_feature_enabled("local_llm_reasoning", "experimental") is True


def test_feature_gate_unknown_feature_and_tier_are_safe() -> None:
    assert is_feature_enabled("does_not_exist", "experimental") is False
    assert is_feature_enabled("backtest_snapshot", "unknown") is False
    assert "rich_cockpit_v2" in enabled_features_for_tier("unknown")

