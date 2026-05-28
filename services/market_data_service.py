from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import pandas as pd

from config import SETTINGS
from infrastructure.providers import FileCacheProvider, MarketDataProvider, MarketDataRequest


@dataclass(frozen=True)
class MarketDataServiceConfig:
    default_period_by_timeframe: dict[str, str]
    interval_by_timeframe: dict[str, str]
    provider_symbol_map: dict[str, str]


class MarketDataService:
    def __init__(
        self,
        provider: MarketDataProvider | None = None,
        service_config: MarketDataServiceConfig | None = None,
    ) -> None:
        self._service_config = service_config or _build_default_service_config()
        self._provider = provider or MarketDataProvider(cache_provider=FileCacheProvider("data/cache"))

    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        normalized_symbol = self.validate_symbol(symbol)
        normalized_timeframe = self.validate_timeframe(timeframe)
        provider_symbol = self._service_config.provider_symbol_map[normalized_symbol]
        interval = self._service_config.interval_by_timeframe[normalized_timeframe]
        period = self._service_config.default_period_by_timeframe[normalized_timeframe]

        request = MarketDataRequest(symbol=provider_symbol, period=period, interval=interval)
        try:
            frame = self._provider.get_market_data(request)
            normalized = _normalize_frame(frame)
            if normalized.empty:
                return self._dummy_frame(interval)
            return normalized
        except Exception:
            return self._dummy_frame(interval)

    def get_supported_symbols(self) -> tuple[str, ...]:
        return SETTINGS.supported_symbols

    def get_supported_timeframes(self) -> tuple[str, ...]:
        return SETTINGS.supported_timeframes

    def get_symbol_categories(self) -> dict[str, tuple[str, ...]]:
        return SYMBOL_CATEGORIES

    def validate_symbol(self, symbol: str) -> str:
        normalized = _normalize_symbol(symbol)
        allowed = set(self.get_supported_symbols())
        if normalized not in allowed:
            allowed_text = ", ".join(sorted(allowed))
            raise ValueError(f"Unsupported symbol: {symbol}. Supported symbols: {allowed_text}")
        return normalized

    def validate_timeframe(self, timeframe: str) -> str:
        normalized = timeframe.strip().upper()
        allowed = set(self.get_supported_timeframes())
        if normalized not in allowed:
            allowed_text = ", ".join(sorted(allowed))
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported timeframes: {allowed_text}")
        return normalized

    def _dummy_frame(self, interval: str, points: int = 200) -> pd.DataFrame:
        step = _interval_to_timedelta(interval)
        now = datetime.now(timezone.utc)
        rows: list[dict[str, float | datetime]] = []
        base = 100.0
        for index in range(points):
            ts = now - (step * (points - index))
            drift = ((index % 24) - 12) * 0.09
            open_price = base + drift
            close_price = open_price + (0.2 if index % 2 == 0 else -0.15)
            high_price = max(open_price, close_price) + 0.25
            low_price = min(open_price, close_price) - 0.25
            rows.append(
                {
                    "Timestamp": ts,
                    "Open": round(open_price, 6),
                    "High": round(high_price, 6),
                    "Low": round(low_price, 6),
                    "Close": round(close_price, 6),
                    "Volume": float(1_500 + (index % 40) * 35),
                }
            )
        frame = pd.DataFrame(rows)
        frame.attrs["source"] = "dummy"
        return frame


def get_market_data(symbol: str, timeframe: str) -> pd.DataFrame:
    return MarketDataService().get_market_data(symbol=symbol, timeframe=timeframe)


def get_supported_symbols() -> tuple[str, ...]:
    return SETTINGS.supported_symbols


def get_supported_timeframes() -> tuple[str, ...]:
    return SETTINGS.supported_timeframes


def get_symbol_categories() -> dict[str, tuple[str, ...]]:
    return SYMBOL_CATEGORIES


def validate_symbol(symbol: str) -> str:
    return MarketDataService().validate_symbol(symbol)


def validate_timeframe(timeframe: str) -> str:
    return MarketDataService().validate_timeframe(timeframe)


def _build_default_service_config() -> MarketDataServiceConfig:
    return MarketDataServiceConfig(
        default_period_by_timeframe={
            "M15": "5d",
            "M30": "5d",
            "H1": "1mo",
            "H4": "3mo",
            "D1": "6mo",
        },
        interval_by_timeframe={
            "M15": "15m",
            "M30": "30m",
            "H1": "1h",
            "H4": "4h",
            "D1": "1d",
        },
        provider_symbol_map={
            "XAUUSD": "GC=F",
            "XAGUSD": "SI=F",
            "USOIL": "CL=F",
            "BTCUSD": "BTC-USD",
            "ETHUSD": "ETH-USD",
            "SOLUSD": "SOL-USD",
            "BNBUSD": "BNB-USD",
            "XRPUSD": "XRP-USD",
            "ADAUSD": "ADA-USD",
            "DOGEUSD": "DOGE-USD",
            "AVAXUSD": "AVAX-USD",
            "LINKUSD": "LINK-USD",
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "USDJPY": "JPY=X",
            "AUDUSD": "AUDUSD=X",
            "USDCAD": "CAD=X",
            "USDCHF": "CHF=X",
            "NZDUSD": "NZDUSD=X",
            "EURJPY": "EURJPY=X",
            "GBPJPY": "GBPJPY=X",
            "AAPL": "AAPL",
            "MSFT": "MSFT",
            "NVDA": "NVDA",
            "TSLA": "TSLA",
            "AMZN": "AMZN",
            "META": "META",
            "GOOGL": "GOOGL",
            "SPY": "SPY",
            "QQQ": "QQQ",
        },
    )


def _normalize_symbol(symbol: str) -> str:
    cleaned = symbol.strip().upper().replace("/", "").replace("-", "")
    return cleaned


def _normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])

    result = frame.copy()
    result.attrs.update(getattr(frame, "attrs", {}))
    required = ["Timestamp", "Open", "High", "Low", "Close"]
    for column in required:
        if column not in result.columns:
            return pd.DataFrame(columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])

    if "Volume" not in result.columns:
        result["Volume"] = 0.0

    result["Timestamp"] = pd.to_datetime(result["Timestamp"], errors="coerce", utc=True)
    for column in ("Open", "High", "Low", "Close", "Volume"):
        result[column] = pd.to_numeric(result[column], errors="coerce")

    result = result.dropna(subset=["Timestamp", "Open", "High", "Low", "Close"])
    result = result.sort_values("Timestamp").reset_index(drop=True)
    normalized = result[["Timestamp", "Open", "High", "Low", "Close", "Volume"]]
    normalized.attrs.update(result.attrs)
    return normalized


def _interval_to_timedelta(interval: str) -> timedelta:
    mapping = {
        "15m": timedelta(minutes=15),
        "30m": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
    }
    return mapping.get(interval, timedelta(hours=1))


SYMBOL_CATEGORIES: dict[str, tuple[str, ...]] = {
    "crypto": ("BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD", "XRPUSD", "ADAUSD", "DOGEUSD", "AVAXUSD", "LINKUSD"),
    "forex": ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "GBPJPY"),
    "commodities": ("XAUUSD", "XAGUSD", "USOIL"),
    "stocks": ("AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOGL", "SPY", "QQQ"),
}


