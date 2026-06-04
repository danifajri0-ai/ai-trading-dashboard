from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/cockpit", tags=["cockpit"])
analyze_cockpit_market = None


class CockpitAnalyzeRequestBody(BaseModel):
    symbol: str
    timeframe: str


@router.post("/analyze")
def analyze_cockpit(body: CockpitAnalyzeRequestBody) -> dict:
    try:
        analyze_cockpit_market_fn = analyze_cockpit_market
        if analyze_cockpit_market_fn is None:
            from services.cockpit_service import analyze_cockpit_market as analyze_cockpit_market_fn

        result = analyze_cockpit_market_fn(symbol=body.symbol, timeframe=body.timeframe)
        return asdict(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Cockpit analysis service is temporarily unavailable. "
                "Please try again in a moment."
            ),
        ) from exc
