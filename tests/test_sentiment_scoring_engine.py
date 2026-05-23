from __future__ import annotations

from domain.cockpit.sentiment_scoring_engine import score_sentiment_inputs


def test_sentiment_scoring_engine_scores_headlines_and_topics() -> None:
    result = score_sentiment_inputs(
        headlines=[
            "Bitcoin rally continues as ETF inflow surge grows",
            "Market optimism rises despite volatility concerns",
        ],
        context=["Macro inflation data expected this week"],
    )

    assert result["status"] == "available"
    assert result["sentiment_score"] is not None
    assert result["label"] in {"Positive", "Neutral", "Negative"}
    assert isinstance(result["key_topics"], list)
    assert isinstance(result["risk_keywords"], list)
    assert result["caveat"]


def test_sentiment_scoring_engine_returns_limited_for_context_only_input() -> None:
    result = score_sentiment_inputs(
        headlines=[],
        context=["Liquidity risk can increase around session change."],
    )

    assert result["status"] == "limited"
    assert result["sentiment_score"] == 50.0
    assert result["label"] == "Neutral"


def test_sentiment_scoring_engine_returns_not_available_without_input() -> None:
    result = score_sentiment_inputs(headlines=[], context=[])

    assert result["status"] == "not_available"
    assert result["sentiment_score"] is None
    assert result["label"] == "Not Available"
