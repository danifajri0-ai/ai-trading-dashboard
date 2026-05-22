from __future__ import annotations

import pandas as pd

from domain.market_regime import detect_liquidity_sweep, detect_simple_fvg, detect_volatility_regime


def test_detect_volatility_regime_values() -> None:
    assert detect_volatility_regime(0) == "Unknown"
    assert detect_volatility_regime(1.5) == "Calm"
    assert detect_volatility_regime(4.0) == "Normal"
    assert detect_volatility_regime(8.0) == "High Volatility"


def test_detect_liquidity_and_fvg_handles_small_data() -> None:
    small = pd.DataFrame({"High": [1.0], "Low": [0.5], "Close": [0.9]})
    assert detect_liquidity_sweep(small) == "Insufficient candles"
    assert detect_simple_fvg(small) == "Insufficient candles"

