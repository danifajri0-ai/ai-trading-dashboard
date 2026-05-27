from __future__ import annotations

from math import isfinite
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = ("Timestamp", "Open", "High", "Low", "Close")


def evaluate_data_quality(
    candles: object,
    timeframe: str | None = None,
    current_time: object = None,
    min_candles: int = 50,
) -> dict[str, Any]:
    frame = _normalize_frame(candles)
    if frame is None:
        return _not_available("OHLCV dataframe is not available.")
    if frame.empty:
        return _not_available("OHLCV dataframe is empty.")

    issues: list[str] = []
    warnings: list[str] = []
    score = 100.0
    source = str(getattr(frame, "attrs", {}).get("source") or "unknown")
    provider_symbol = getattr(frame, "attrs", {}).get("provider_symbol")

    if source == "dummy":
        issues.append("Synthetic fallback data is active because live market data was unavailable.")
        score -= 40.0

    if len(frame) < min_candles:
        issues.append(f"Insufficient candles: {len(frame)} available, {min_candles} required.")
        score -= 25.0

    invalid_ohlc_count = _invalid_ohlc_count(frame)
    if invalid_ohlc_count:
        issues.append(f"Invalid OHLC rows detected: {invalid_ohlc_count}.")
        score -= min(35.0, invalid_ohlc_count * 5.0)

    missing_data_detected = _missing_data_detected(frame, timeframe)
    duplicate_timestamps = _duplicate_timestamps(frame)
    if missing_data_detected:
        issues.append("Missing candle gap detected.")
        score -= 20.0
    if duplicate_timestamps:
        issues.append("Duplicate candle timestamps detected.")
        score -= 15.0

    stale_data = _stale_data_detected(frame, timeframe, current_time)
    if stale_data:
        issues.append("Latest candle is stale for expected timeframe.")
        score -= 25.0

    volume_issue = _volume_issue_detected(frame)
    if volume_issue:
        warnings.append("Volume is missing, negative, or mostly zero.")
        score -= 10.0

    score = _clamp_score(score)
    status = "available" if not issues and not warnings else "caution"

    return {
        "status": status,
        "score": score,
        "missing_data_detected": missing_data_detected,
        "stale_data_detected": stale_data,
        "invalid_ohlc_detected": invalid_ohlc_count > 0,
        "volume_issue_detected": volume_issue,
        "insufficient_candles": len(frame) < min_candles,
        "duplicate_timestamp_detected": duplicate_timestamps,
        "candle_count": int(len(frame)),
        "source": source,
        "provider_symbol": provider_symbol,
        "issues": issues,
        "warnings": warnings,
    }


def _not_available(reason: str) -> dict[str, Any]:
    return {
        "status": "not_available",
        "score": 0.0,
        "missing_data_detected": False,
        "stale_data_detected": False,
        "invalid_ohlc_detected": False,
        "volume_issue_detected": False,
        "insufficient_candles": True,
        "duplicate_timestamp_detected": False,
        "candle_count": 0,
        "source": "not_available",
        "provider_symbol": None,
        "issues": [reason],
        "warnings": [],
    }


def _normalize_frame(candles: object) -> pd.DataFrame | None:
    if not isinstance(candles, pd.DataFrame):
        return None
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in candles.columns]
    if missing_columns:
        return None

    frame = candles.copy()
    frame.attrs.update(getattr(candles, "attrs", {}))
    if "Volume" not in frame.columns:
        frame["Volume"] = pd.NA
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], errors="coerce", utc=True)
    for column in ("Open", "High", "Low", "Close", "Volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)
    frame.attrs.update(getattr(candles, "attrs", {}))
    return frame


def _invalid_ohlc_count(frame: pd.DataFrame) -> int:
    prices = frame[["Open", "High", "Low", "Close"]]
    finite_mask = prices.map(_is_finite)
    valid_numbers = finite_mask.all(axis=1)
    positive_prices = (prices > 0).all(axis=1)
    high_is_valid = frame["High"] >= frame[["Open", "Close", "Low"]].max(axis=1)
    low_is_valid = frame["Low"] <= frame[["Open", "Close", "High"]].min(axis=1)
    valid_rows = valid_numbers & positive_prices & high_is_valid & low_is_valid
    return int((~valid_rows).sum())


def _missing_data_detected(frame: pd.DataFrame, timeframe: str | None) -> bool:
    if len(frame) < 3:
        return False
    step = _expected_step(timeframe)
    diffs = frame["Timestamp"].diff().dropna()
    if diffs.empty:
        return False
    return bool((diffs > step * 1.5).any())


def _duplicate_timestamps(frame: pd.DataFrame) -> bool:
    return bool(frame["Timestamp"].duplicated().any())


def _stale_data_detected(frame: pd.DataFrame, timeframe: str | None, current_time: object) -> bool:
    latest = frame["Timestamp"].iloc[-1]
    now = _safe_timestamp(current_time) or pd.Timestamp.now(tz="UTC")
    age = now - latest
    if age < -pd.Timedelta(minutes=5):
        return True
    return bool(age > _expected_step(timeframe) * 3)


def _volume_issue_detected(frame: pd.DataFrame) -> bool:
    volume = pd.to_numeric(frame["Volume"], errors="coerce")
    if volume.isna().any() or (volume < 0).any():
        return True
    if len(volume) == 0:
        return True
    zero_ratio = float((volume == 0).sum()) / float(len(volume))
    return zero_ratio >= 0.8


def _expected_step(timeframe: str | None) -> pd.Timedelta:
    mapping = {
        "M15": pd.Timedelta(minutes=15),
        "M30": pd.Timedelta(minutes=30),
        "H1": pd.Timedelta(hours=1),
        "H4": pd.Timedelta(hours=4),
        "D1": pd.Timedelta(days=1),
    }
    if timeframe is None:
        return pd.Timedelta(hours=1)
    return mapping.get(timeframe.upper(), pd.Timedelta(hours=1))


def _safe_timestamp(value: object) -> pd.Timestamp | None:
    if value is None:
        return None
    timestamp = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(timestamp):
        return None
    return timestamp


def _is_finite(value: object) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return isfinite(number)


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 2)
