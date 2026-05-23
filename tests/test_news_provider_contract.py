from __future__ import annotations

from infrastructure.providers.news_provider import NewsProvider


class StubExternalNewsProvider:
    def __init__(self, payload):
        self.payload = payload

    def get_news(self, symbol: str, asset_class: str):  # noqa: ARG002
        return dict(self.payload)


def test_news_provider_returns_limited_in_local_mode_without_external_access() -> None:
    provider = NewsProvider(enable_external_provider=False)

    result = provider.get_news("BTCUSD", "crypto")

    assert result["status"] == "limited"
    assert result["items"] == []
    assert result["reason"]


def test_news_provider_normalizes_external_payload_contract() -> None:
    provider = NewsProvider(
        external_provider=StubExternalNewsProvider(
            {
                "status": "available",
                "source": "stub_feed",
                "items": [
                    {"headline": "Bitcoin ETF inflow rises", "source": "Stub", "published_at": None, "url": None},
                    {"headline": "", "source": "Stub"},
                ],
            }
        ),
        enable_external_provider=True,
    )

    result = provider.get_news("BTCUSD", "crypto")

    assert result["status"] == "available"
    assert len(result["items"]) == 1
    assert result["items"][0]["headline"] == "Bitcoin ETF inflow rises"


def test_news_provider_returns_not_available_when_external_fails() -> None:
    class FailingExternalNewsProvider:
        def get_news(self, symbol: str, asset_class: str):  # noqa: ARG002
            raise RuntimeError("network failed")

    provider = NewsProvider(
        external_provider=FailingExternalNewsProvider(),
        enable_external_provider=True,
    )

    result = provider.get_news("BTCUSD", "crypto")

    assert result["status"] == "not_available"
    assert result["items"] == []
    assert "failed" in str(result["reason"]).lower()
