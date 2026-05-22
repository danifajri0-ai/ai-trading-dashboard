from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any
from urllib.parse import quote_plus
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from infrastructure.providers.cache_provider import FileCacheProvider


@dataclass(frozen=True)
class NewsItem:
    title: str
    source: str
    sentiment_score: float


class NewsProvider:
    def __init__(self, cache_provider: FileCacheProvider | None = None, cache_ttl_seconds: int = 300) -> None:
        self.cache_provider = cache_provider
        self.cache_ttl_seconds = cache_ttl_seconds

    def get_news_snapshot(self, symbol: str, limit: int = 5) -> dict[str, Any]:
        cache_key = f"news_{symbol}_{limit}"
        if self.cache_provider is not None:
            cached = self.cache_provider.get(cache_key)
            if cached is not None:
                return cached

        items: list[NewsItem]
        source: str
        try:
            items = self._fetch_yahoo_rss(symbol, limit=limit)
            source = "yahoo_rss"
        except Exception:
            items = self._dummy_news(symbol, limit=limit)
            source = "dummy"

        overall = _aggregate_sentiment(items)
        payload = {
            "symbol": symbol,
            "source": source,
            "overall_sentiment": overall["label"],
            "overall_score": overall["score"],
            "items": [
                {"title": item.title, "source": item.source, "sentiment_score": item.sentiment_score}
                for item in items
            ],
        }
        if self.cache_provider is not None:
            self.cache_provider.set(cache_key, payload, ttl_seconds=self.cache_ttl_seconds)
        return payload

    def _fetch_yahoo_rss(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        query = quote_plus(symbol)
        url = f"https://news.search.yahoo.com/rss?p={query}"
        with urlopen(url, timeout=8) as response:
            xml_content = response.read()

        root = ET.fromstring(xml_content)
        items: list[NewsItem] = []
        for item in root.findall("./channel/item"):
            title = (item.findtext("title") or "").strip()
            source = (item.findtext("source") or "Yahoo News").strip()
            if not title:
                continue
            score = _score_headline(title)
            items.append(NewsItem(title=title, source=source, sentiment_score=score))
            if len(items) >= limit:
                break

        if not items:
            raise RuntimeError("RSS returned no news items.")
        return items

    def _dummy_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        templates = [
            f"{symbol} market awaits key macro data release",
            f"{symbol} volatility rises ahead of central bank remarks",
            f"Traders monitor {symbol} liquidity during active session",
            f"{symbol} price action mixed as risk appetite shifts",
            f"Analysts watch support and resistance zones on {symbol}",
        ]
        items: list[NewsItem] = []
        for title in templates[: max(1, limit)]:
            items.append(NewsItem(title=title, source="dummy_feed", sentiment_score=_score_headline(title)))
        return items


def _score_headline(title: str) -> float:
    positive_words = {"surge", "gain", "beats", "optimism", "rally", "strong", "growth"}
    negative_words = {"drop", "fall", "misses", "risk", "fear", "weak", "decline", "volatility"}
    tokens = re.findall(r"[a-zA-Z]+", title.lower())
    score = 50.0
    for token in tokens:
        if token in positive_words:
            score += 6.0
        elif token in negative_words:
            score -= 6.0
    return max(0.0, min(100.0, score))


def _aggregate_sentiment(items: list[NewsItem]) -> dict[str, Any]:
    if not items:
        return {"label": "Neutral", "score": 50.0}
    avg = sum(item.sentiment_score for item in items) / len(items)
    if avg >= 60:
        label = "Positive"
    elif avg <= 40:
        label = "Negative"
    else:
        label = "Neutral"
    return {"label": label, "score": round(avg, 2)}

