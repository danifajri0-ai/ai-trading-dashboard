from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from infrastructure.providers.cache_provider import FileCacheProvider
from market_data import fetch_market_data


@dataclass(frozen=True)
class MarketDataRequest:
    symbol: str
    period: str
    interval: str


class MarketDataProvider:
    def __init__(self, cache_provider: FileCacheProvider | None = None, cache_ttl_seconds: int = 120) -> None:
        self.cache_provider = cache_provider
        self.cache_ttl_seconds = cache_ttl_seconds

    def get_market_data(self, request: MarketDataRequest) -> pd.DataFrame:
        cache_key = f"market_{request.symbol}_{request.period}_{request.interval}"
        if self.cache_provider is not None:
            cached = self.cache_provider.get(cache_key)
            if cached is not None:
                frame = _frame_from_payload(cached)
                if not frame.empty:
                    return frame

        try:
            frame = fetch_market_data(request.symbol, request.period, request.interval)
            source = "live"
        except Exception:
            frame = self._build_dummy_ohlcv(request.interval, points=200)
            source = "dummy"

        if self.cache_provider is not None and not frame.empty:
            payload = _frame_to_payload(frame)
            payload["_meta"] = {"source": source}
            self.cache_provider.set(cache_key, payload, ttl_seconds=self.cache_ttl_seconds)

        return frame

    def _build_dummy_ohlcv(self, interval: str, points: int = 200) -> pd.DataFrame:
        step = _interval_to_timedelta(interval)
        now = datetime.now(timezone.utc)
        rows: list[dict[str, Any]] = []
        base = 100.0

        for index in range(points):
            ts = now - (step * (points - index))
            drift = ((index % 20) - 10) * 0.08
            open_price = base + drift
            close_price = open_price + (0.15 if index % 2 == 0 else -0.12)
            high_price = max(open_price, close_price) + 0.2
            low_price = min(open_price, close_price) - 0.2
            rows.append(
                {
                    "Timestamp": ts,
                    "Open": round(open_price, 6),
                    "High": round(high_price, 6),
                    "Low": round(low_price, 6),
                    "Close": round(close_price, 6),
                    "Volume": float(1_000 + (index % 25) * 40),
                }
            )

        return pd.DataFrame(rows)


def _interval_to_timedelta(interval: str) -> timedelta:
    mapping = {
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "30m": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
        "M15": timedelta(minutes=15),
        "M30": timedelta(minutes=30),
        "H1": timedelta(hours=1),
        "H4": timedelta(hours=4),
        "D1": timedelta(days=1),
    }
    return mapping.get(interval, timedelta(hours=1))


def _frame_to_payload(frame: pd.DataFrame) -> dict[str, Any]:
    serializable = frame.copy()
    if "Timestamp" in serializable.columns:
        serializable["Timestamp"] = pd.to_datetime(serializable["Timestamp"], errors="coerce").astype(str)
    return {"rows": serializable.to_dict(orient="records")}


def _frame_from_payload(payload: dict[str, Any]) -> pd.DataFrame:
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    if "Timestamp" in frame.columns:
        frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], errors="coerce", utc=True)
    return frame

