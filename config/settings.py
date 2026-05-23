from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Literal

AppMode = Literal["local_service", "http_api"]


@dataclass(frozen=True)
class IndicatorSettings:
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    atr_period: int = 14
    moving_average_period: int = 50


@dataclass(frozen=True)
class RiskSettings:
    default_risk_per_trade: float = 0.01
    minimum_risk_reward: float = 2.0
    maximum_allowed_risk_level: float = 0.03


@dataclass(frozen=True)
class SupabaseSettings:
    enabled: bool = False
    url: str = ""
    service_role_key: str = ""
    anon_key: str = ""


@dataclass(frozen=True)
class TradingDashboardSettings:
    mode: AppMode = "local_service"
    api_base_url: str = "http://127.0.0.1:8000"
    allowed_origins: tuple[str, ...] = ("http://localhost:3000", "http://127.0.0.1:3000")
    supported_symbols: tuple[str, ...] = (
        "XAUUSD",
        "BTCUSD",
        "ETHUSD",
        "SOLUSD",
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "AUDUSD",
        "USDCAD",
    )
    supported_timeframes: tuple[str, ...] = ("M15", "M30", "H1", "H4", "D1")
    indicators: IndicatorSettings = IndicatorSettings()
    risk: RiskSettings = RiskSettings()
    supabase: SupabaseSettings = SupabaseSettings()


def _load_settings() -> TradingDashboardSettings:
    mode = _normalize_mode(os.getenv("API_MODE"))
    api_base_url = _env_text("API_BASE_URL", "http://127.0.0.1:8000")
    allowed_origins = _csv_tuple(os.getenv("ALLOWED_ORIGINS")) or ("http://localhost:3000", "http://127.0.0.1:3000")
    supabase = SupabaseSettings(
        enabled=_env_bool(os.getenv("SUPABASE_ENABLED"), default=False),
        url=_env_text("SUPABASE_URL", ""),
        service_role_key=_env_text("SUPABASE_SERVICE_ROLE_KEY", ""),
        anon_key=_env_text("SUPABASE_ANON_KEY", ""),
    )
    return TradingDashboardSettings(
        mode=mode,
        api_base_url=api_base_url,
        allowed_origins=allowed_origins,
        supabase=supabase,
    )


def _normalize_mode(value: str | None) -> AppMode:
    normalized = str(value or "local_service").strip().lower()
    if normalized in {"local_service", "http_api"}:
        return normalized  # type: ignore[return-value]
    return "local_service"


def _env_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _env_text(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def _csv_tuple(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    items = [item.strip() for item in value.split(",") if item.strip()]
    return tuple(items)


SETTINGS = _load_settings()

