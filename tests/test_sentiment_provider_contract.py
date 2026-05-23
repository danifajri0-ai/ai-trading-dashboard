from __future__ import annotations

from infrastructure.providers.sentiment_provider import SentimentProvider


class StubNewsProvider:
    def __init__(self, payload):
        self.payload = payload

    def get_news(self, symbol: str, asset_class: str):  # noqa: ARG002
        return dict(self.payload)


def test_sentiment_provider_maps_available_news_to_headlines_and_context() -> None:
    provider = SentimentProvider(
        news_provider=StubNewsProvider(
            {
                "status": "available",
                "source": "stub",
                "items": [{"headline": "EUR/USD gains as inflation cools"}],
            }
        )
    )

    result = provider.get_sentiment_inputs("EURUSD", "forex")

    assert result["status"] == "available"
    assert result["headlines"] == ["EUR/USD gains as inflation cools"]
    assert result["context"]


def test_sentiment_provider_keeps_limited_when_news_is_limited() -> None:
    provider = SentimentProvider(
        news_provider=StubNewsProvider(
            {"status": "limited", "source": "stub", "items": [], "reason": "disabled"}
        )
    )

    result = provider.get_sentiment_inputs("BTCUSD", "crypto")

    assert result["status"] == "limited"
    assert result["headlines"] == []
    assert result["reason"] == "disabled"
