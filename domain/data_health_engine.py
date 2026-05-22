from __future__ import annotations

import pandas as pd


def evaluate_data_health(
    candles: object = None,
    expected_timeframe: str | None = None,
    latest_timestamp: object = None,
    current_time: object = None,
) -> dict[str, object]:
    frame = _normalize_frame(candles)
    latest = _safe_timestamp(latest_timestamp)
    if latest is None and frame is not None and not frame.empty:
        latest = _safe_timestamp(frame["Timestamp"].iloc[-1])

    now = _safe_timestamp(current_time) or pd.Timestamp.now(tz="UTC")
    step = _expected_step(expected_timeframe)

    if latest is None:
        return _unavailable("required inputs missing")

    duplicate_detected = _has_duplicate_candle(frame)
    missing_detected = _has_missing_candle(frame, step)
    fresh = _is_fresh(latest, now, step)

    warnings: list[str] = []
    if not fresh:
        warnings.append("Latest candle is stale for expected timeframe.")
    if duplicate_detected:
        warnings.append("Duplicate candle timestamps detected.")
    if missing_detected:
        warnings.append("Potential missing candle gap detected.")

    status = "ok" if not warnings else "warning"
    return {
        "status": status,
        "data_is_fresh": fresh,
        "missing_candle_detected": missing_detected,
        "duplicate_candle_detected": duplicate_detected,
        "last_candle_time": latest.isoformat(),
        "warnings": warnings,
    }


def _unavailable(reason: str) -> dict[str, object]:
    return {
        "status": "unavailable",
        "reason": reason,
        "data_is_fresh": False,
        "missing_candle_detected": False,
        "duplicate_candle_detected": False,
        "last_candle_time": None,
        "warnings": [reason],
    }


def _normalize_frame(candles: object) -> pd.DataFrame | None:
    if isinstance(candles, pd.DataFrame):
        frame = candles.copy()
        if "Timestamp" in frame.columns:
            frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], errors="coerce", utc=True)
            frame = frame.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)
        return frame
    return None


def _safe_timestamp(value: object) -> pd.Timestamp | None:
    if value is None:
        return None
    try:
        ts = pd.to_datetime(value, errors="coerce", utc=True)
    except Exception:
        return None
    if pd.isna(ts):
        return None
    return ts


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


def _has_duplicate_candle(frame: pd.DataFrame | None) -> bool:
    if frame is None or frame.empty or "Timestamp" not in frame.columns:
        return False
    return bool(frame["Timestamp"].duplicated().any())


def _has_missing_candle(frame: pd.DataFrame | None, step: pd.Timedelta) -> bool:
    if frame is None or len(frame) < 3 or "Timestamp" not in frame.columns:
        return False
    diffs = frame["Timestamp"].diff().dropna()
    if diffs.empty:
        return False
    # Allow jitter up to 50% of expected cadence.
    threshold = step * 1.5
    return bool((diffs > threshold).any())


def _is_fresh(latest: pd.Timestamp, now: pd.Timestamp, step: pd.Timedelta) -> bool:
    age = now - latest
    if age < -pd.Timedelta(minutes=5):
        return False
    return age <= (step * 3)
