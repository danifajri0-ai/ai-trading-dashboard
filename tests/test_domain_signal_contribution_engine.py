from __future__ import annotations

from domain.signal_contribution_engine import build_signal_contribution_lite


def test_signal_contribution_builds_weighted_final_score() -> None:
    result = build_signal_contribution_lite(
        trend_score=80,
        momentum_score=70,
        volume_score=60,
        volatility_score=50,
        structure_score=40,
    )

    assert result["status"] == "available"
    assert isinstance(result["final_score"], float)
    assert 0 <= result["final_score"] <= 100
    assert result["missing_factors"] == []
    assert "trend" in result["positive_factors"]


def test_signal_contribution_tracks_missing_factors_without_error() -> None:
    result = build_signal_contribution_lite(
        trend_score=80,
        momentum_score=None,
        volume_score="bad-value",
        volatility_score=55,
        structure_score=None,
    )

    assert result["status"] == "available"
    assert set(result["missing_factors"]) == {"momentum", "volume", "structure"}
    assert result["contributions"]["momentum"]["score"] is None
    assert 0 <= result["final_score"] <= 100


def test_signal_contribution_marks_negative_factors() -> None:
    result = build_signal_contribution_lite(
        trend_score=25,
        momentum_score=30,
        volume_score=75,
        volatility_score=35,
        structure_score=80,
    )

    assert "trend" in result["negative_factors"]
    assert "momentum" in result["negative_factors"]
    assert "volatility" in result["negative_factors"]
