from __future__ import annotations

import pandas as pd
import pytest

from services.market_data_service import MarketDataService


def test_supported_symbols_and_timeframes_are_available() -> None:
    service = MarketDataService()
    assert "BTCUSD" in service.get_supported_symbols()
    assert "H1" in service.get_supported_timeframes()


def test_validate_symbol_and_timeframe() -> None:
    service = MarketDataService()
    assert service.validate_symbol("btc/usd") == "BTCUSD"
    assert service.validate_timeframe("h1") == "H1"

    with pytest.raises(ValueError):
        service.validate_symbol("INVALID")
    with pytest.raises(ValueError):
        service.validate_timeframe("M1")


def test_get_market_data_returns_consistent_columns() -> None:
    service = MarketDataService()
    frame = service.get_market_data("BTCUSD", "H1")
    assert isinstance(frame, pd.DataFrame)
    assert list(frame.columns) == ["Timestamp", "Open", "High", "Low", "Close", "Volume"]
    assert len(frame) > 0

