from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from infrastructure.providers.news_provider import NewsProvider, NewsProviderContract


@dataclass(frozen=True)
class SentimentProvider:
    news_provider: NewsProviderContract

    def get_sentiment_inputs(self, symbol: str, asset_class: str) -> dict[str, Any]:
        news_payload = self.news_provider.get_news(symbol=symbol, asset_class=asset_class)
        status = str(news_payload.get("status", "not_available"))
        items = news_payload.get("items", [])
        context = _context_for_asset(symbol, asset_class)

        if status == "available":
            return {
                "status": "available",
                "symbol": symbol,
                "asset_class": asset_class,
                "headlines": [str(item.get("headline", "")) for item in items if isinstance(item, dict)],
                "context": context,
                "source": str(news_payload.get("source", "news_provider")),
                "reason": None,
            }

        if status == "limited":
            return {
                "status": "limited",
                "symbol": symbol,
                "asset_class": asset_class,
                "headlines": [],
                "context": context,
                "source": str(news_payload.get("source", "news_provider")),
                "reason": str(news_payload.get("reason") or "News unavailable in limited mode."),
            }

        return {
            "status": "not_available",
            "symbol": symbol,
            "asset_class": asset_class,
            "headlines": [],
            "context": context,
            "source": str(news_payload.get("source", "news_provider")),
            "reason": str(news_payload.get("reason") or "News is not available."),
        }


def build_default_sentiment_provider(enable_external_provider: bool = False) -> SentimentProvider:
    return SentimentProvider(
        news_provider=NewsProvider(enable_external_provider=enable_external_provider),
    )


def _context_for_asset(symbol: str, asset_class: str) -> list[str]:
    normalized_asset = asset_class.lower()
    if normalized_asset == "crypto":
        return [
            f"{symbol} can react quickly to risk appetite and liquidity shifts.",
            "Crypto narratives can change rapidly during high volatility windows.",
        ]
    if normalized_asset == "forex":
        return [
            f"{symbol} is sensitive to macro data surprises and central bank tone.",
            "Session overlap often affects intraday liquidity and spread behavior.",
        ]
    if normalized_asset == "commodity":
        return [
            f"{symbol} can be impacted by USD strength and global risk sentiment.",
        ]
    return [f"{symbol} sentiment context is currently generic due to limited asset metadata."]
