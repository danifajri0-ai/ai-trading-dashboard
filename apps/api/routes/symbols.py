from __future__ import annotations

from fastapi import APIRouter

from services.market_data_service import get_supported_symbols, get_supported_timeframes

router = APIRouter(tags=["symbols"])


@router.get("/symbols")
def list_symbols() -> dict[str, list[str]]:
    return {
        "symbols": list(get_supported_symbols()),
        "timeframes": list(get_supported_timeframes()),
    }

