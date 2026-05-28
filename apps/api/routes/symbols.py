from __future__ import annotations

from fastapi import APIRouter

from services.market_data_service import get_supported_symbols, get_supported_timeframes, get_symbol_categories

router = APIRouter(tags=["symbols"])


@router.get("/symbols")
def list_symbols() -> dict[str, object]:
    return {
        "symbols": list(get_supported_symbols()),
        "timeframes": list(get_supported_timeframes()),
        "categories": {name: list(symbols) for name, symbols in get_symbol_categories().items()},
    }

