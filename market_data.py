from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd
import yfinance as yf


PAIRS: dict[str, str] = {
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "XAU/USD": "GC=F",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
}

PERIODS: tuple[str, ...] = ("1d", "5d", "1mo", "3mo", "6mo", "1y")
INTERVALS: tuple[str, ...] = ("5m", "15m", "30m", "1h", "1d")

# Yahoo Finance has practical limits for intraday data. Keeping the UI inside
# these combinations avoids the most common empty responses.
INTERVAL_PERIODS: dict[str, tuple[str, ...]] = {
    "5m": ("1d", "5d", "1mo"),
    "15m": ("1d", "5d", "1mo"),
    "30m": ("1d", "5d", "1mo"),
    "1h": ("1d", "5d", "1mo", "3mo", "6mo"),
    "1d": PERIODS,
}

REQUIRED_PRICE_COLUMNS: tuple[str, ...] = ("Open", "High", "Low", "Close")


@dataclass(frozen=True)
class MarketRequest:
    label: str
    symbol: str
    period: str
    interval: str


class MarketDataError(RuntimeError):
    """Raised when market data cannot be loaded or normalized."""


def get_symbol(pair_label: str) -> str:
    try:
        return PAIRS[pair_label]
    except KeyError as exc:
        raise MarketDataError(f"Pair tidak dikenal: {pair_label}") from exc


def compatible_periods(interval: str) -> tuple[str, ...]:
    return INTERVAL_PERIODS.get(interval, PERIODS)


def normalize_market_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    if raw_data is None or raw_data.empty:
        return pd.DataFrame()

    data = raw_data.copy()

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()

    time_column = _resolve_time_column(data.columns)
    if time_column is not None:
        data = data.rename(columns={time_column: "Timestamp"})
    elif "Timestamp" not in data.columns:
        data.insert(0, "Timestamp", range(len(data)))

    missing_columns = [col for col in REQUIRED_PRICE_COLUMNS if col not in data.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise MarketDataError(f"Kolom data tidak lengkap: {missing}")

    for column in REQUIRED_PRICE_COLUMNS + ("Volume",):
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(subset=list(REQUIRED_PRICE_COLUMNS))
    data = data.sort_values("Timestamp").reset_index(drop=True)

    return data


def fetch_market_data(symbol: str, period: str, interval: str) -> pd.DataFrame:
    try:
        raw_data = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False,
            threads=False,
        )
    except Exception as exc:  # yfinance can raise several transport exceptions.
        raise MarketDataError(f"Gagal mengambil data dari Yahoo Finance: {exc}") from exc

    data = normalize_market_data(raw_data)
    if data.empty:
        raise MarketDataError("Data kosong. Coba pair, periode, atau timeframe lain.")

    return data


def validate_request(request: MarketRequest) -> None:
    if request.symbol not in PAIRS.values():
        raise MarketDataError(f"Symbol tidak didukung: {request.symbol}")

    if request.interval not in INTERVALS:
        raise MarketDataError(f"Timeframe tidak didukung: {request.interval}")

    allowed_periods = compatible_periods(request.interval)
    if request.period not in allowed_periods:
        allowed = ", ".join(allowed_periods)
        raise MarketDataError(
            f"Periode {request.period} kurang cocok untuk timeframe {request.interval}. "
            f"Gunakan salah satu: {allowed}."
        )


def _resolve_time_column(columns: Iterable[object]) -> object | None:
    normalized = {str(column).lower(): column for column in columns}
    for candidate in ("datetime", "date", "timestamp"):
        if candidate in normalized:
            return normalized[candidate]
    return None
