from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd


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

BINANCE_SYMBOLS: dict[str, str] = {
    "BTC-USD": "BTCUSDT",
    "ETH-USD": "ETHUSDT",
}

BINANCE_INTERVAL_MILLISECONDS: dict[str, int] = {
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "1d": 86_400_000,
}

PERIOD_SECONDS: dict[str, int] = {
    "1d": 86_400,
    "5d": 432_000,
    "1mo": 2_592_000,
    "3mo": 7_776_000,
    "6mo": 15_552_000,
    "1y": 31_536_000,
}


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
    if symbol in BINANCE_SYMBOLS:
        try:
            data = fetch_binance_klines(BINANCE_SYMBOLS[symbol], period, interval)
            if not data.empty:
                return data
        except Exception:
            # Binance may be blocked in some networks/regions. Yahoo remains the
            # cloud-safe fallback for the public demo.
            pass

    try:
        import yfinance as yf

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


def data_source_label(symbol: str) -> str:
    if symbol in BINANCE_SYMBOLS:
        return "Binance Public Klines / Yahoo Fallback"
    return "Yahoo Finance Snapshot"


def fetch_binance_klines(symbol: str, period: str, interval: str) -> pd.DataFrame:
    seconds = PERIOD_SECONDS.get(period, PERIOD_SECONDS["1mo"])
    start_time = int((time.time() - seconds) * 1000)
    end_time = int(time.time() * 1000)
    interval_ms = BINANCE_INTERVAL_MILLISECONDS.get(interval, 3_600_000)
    rows: list[list[object]] = []
    cursor = start_time
    max_pages = 12

    for _ in range(max_pages):
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": cursor,
            "endTime": end_time,
            "limit": 1000,
        }
        url = f"https://api.binance.com/api/v3/klines?{urlencode(params)}"
        with urlopen(url, timeout=10) as response:
            page_rows = json.loads(response.read().decode("utf-8"))

        if not page_rows:
            break

        rows.extend(page_rows)
        last_open_time = int(page_rows[-1][0])
        next_cursor = last_open_time + interval_ms
        if next_cursor <= cursor or next_cursor >= end_time or len(page_rows) < 1000:
            break
        cursor = next_cursor

    if not rows:
        return pd.DataFrame()

    data = pd.DataFrame(
        rows,
        columns=[
            "OpenTime",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "CloseTime",
            "QuoteAssetVolume",
            "TradeCount",
            "TakerBuyBaseVolume",
            "TakerBuyQuoteVolume",
            "Ignore",
        ],
    )
    data = data.rename(columns={"OpenTime": "Timestamp"})
    data["Timestamp"] = pd.to_datetime(data["Timestamp"], unit="ms", utc=True)

    for column in ("Open", "High", "Low", "Close", "Volume"):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data[["Timestamp", "Open", "High", "Low", "Close", "Volume"]]
    data = data.dropna(subset=list(REQUIRED_PRICE_COLUMNS))
    data = data.drop_duplicates(subset=["Timestamp"], keep="last")
    return data.sort_values("Timestamp").reset_index(drop=True)


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
