from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import quote_plus
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from infrastructure.providers.cache_provider import FileCacheProvider


@dataclass(frozen=True)
class NewsItem:
    headline: str
    source: str
    published_at: str | None = None
    url: str | None = None


class NewsProviderContract(Protocol):
    def get_news(self, symbol: str, asset_class: str) -> dict[str, Any]:
        ...


class YahooRssNewsProvider:
    def __init__(self, timeout_seconds: int = 6) -> None:
        self.timeout_seconds = timeout_seconds

    def get_news(self, symbol: str, asset_class: str) -> dict[str, Any]:
        query = quote_plus(_query_for_symbol(symbol, asset_class))
        url = f"https://news.search.yahoo.com/rss?p={query}"
        with urlopen(url, timeout=self.timeout_seconds) as response:
            xml_content = response.read()

        root = ET.fromstring(xml_content)
        items: list[NewsItem] = []
        for item in root.findall("./channel/item"):
            headline = (item.findtext("title") or "").strip()
            source = (item.findtext("source") or "Yahoo News").strip()
            published_at = (item.findtext("pubDate") or "").strip() or None
            article_url = (item.findtext("link") or "").strip() or None
            if not headline:
                continue
            items.append(
                NewsItem(
                    headline=headline,
                    source=source,
                    published_at=published_at,
                    url=article_url,
                )
            )

        if not items:
            return _not_available(symbol, asset_class, "RSS returned no items.")
        return _available(symbol, asset_class, items, source="yahoo_rss")


class NewsProvider:
    def __init__(
        self,
        cache_provider: FileCacheProvider | None = None,
        external_provider: NewsProviderContract | None = None,
        enable_external_provider: bool = False,
        max_items: int = 8,
        cache_ttl_seconds: int = 180,
    ) -> None:
        self.cache_provider = cache_provider
        self.external_provider = external_provider or YahooRssNewsProvider()
        self.enable_external_provider = enable_external_provider
        self.max_items = max_items
        self.cache_ttl_seconds = cache_ttl_seconds

    def get_news(self, symbol: str, asset_class: str) -> dict[str, Any]:
        cache_key = f"news_v2_{symbol}_{asset_class}_{self.max_items}"
        if self.cache_provider is not None:
            cached = self.cache_provider.get(cache_key)
            if isinstance(cached, dict):
                return cached

        if not self.enable_external_provider:
            payload = _limited(symbol, asset_class, "External news provider disabled in local/dev mode.")
            if self.cache_provider is not None:
                self.cache_provider.set(cache_key, payload, ttl_seconds=self.cache_ttl_seconds)
            return payload

        try:
            raw = self.external_provider.get_news(symbol, asset_class)
        except Exception as exc:
            raw = _not_available(symbol, asset_class, f"External news provider failed: {exc}")

        payload = _normalize_payload(raw, symbol, asset_class, self.max_items)
        if self.cache_provider is not None:
            self.cache_provider.set(cache_key, payload, ttl_seconds=self.cache_ttl_seconds)
        return payload


def _normalize_payload(raw: dict[str, Any], symbol: str, asset_class: str, max_items: int) -> dict[str, Any]:
    status = str(raw.get("status", "")).lower()
    if status not in {"available", "limited", "not_available"}:
        status = "not_available"

    items: list[dict[str, Any]] = []
    source = str(raw.get("source", "unknown"))
    for item in raw.get("items", []):
        if not isinstance(item, dict):
            continue
        headline = str(item.get("headline", "")).strip()
        if not headline:
            continue
        items.append(
            {
                "headline": headline,
                "source": str(item.get("source", source)),
                "published_at": item.get("published_at"),
                "url": item.get("url"),
            }
        )
        if len(items) >= max_items:
            break

    if status == "available" and not items:
        status = "not_available"
    if status == "not_available":
        items = []

    reason = raw.get("reason")
    return {
        "status": status,
        "symbol": symbol,
        "asset_class": asset_class,
        "source": source,
        "items": items,
        "reason": str(reason) if reason else None,
    }


def _query_for_symbol(symbol: str, asset_class: str) -> str:
    normalized = symbol.upper().strip()
    if asset_class.lower() == "crypto" and normalized.endswith("USD") and len(normalized) > 3:
        return f"{normalized[:-3]} USD crypto"
    if asset_class.lower() == "forex" and normalized.endswith("USD") and len(normalized) > 3:
        return f"{normalized[:-3]}/USD forex"
    return normalized


def _available(symbol: str, asset_class: str, items: list[NewsItem], source: str) -> dict[str, Any]:
    return {
        "status": "available",
        "symbol": symbol,
        "asset_class": asset_class,
        "source": source,
        "items": [
            {
                "headline": item.headline,
                "source": item.source,
                "published_at": item.published_at,
                "url": item.url,
            }
            for item in items
        ],
        "reason": None,
    }


def _limited(symbol: str, asset_class: str, reason: str) -> dict[str, Any]:
    return {
        "status": "limited",
        "symbol": symbol,
        "asset_class": asset_class,
        "source": "local_mode",
        "items": [],
        "reason": reason,
    }


def _not_available(symbol: str, asset_class: str, reason: str) -> dict[str, Any]:
    return {
        "status": "not_available",
        "symbol": symbol,
        "asset_class": asset_class,
        "source": "external_provider",
        "items": [],
        "reason": reason,
    }
