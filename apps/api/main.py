from __future__ import annotations

from fastapi import FastAPI

from apps.api.routes import analysis_router, cockpit_router, health_router, persistence_router, symbols_router


app = FastAPI(
    title="Trading Dashboard API",
    version="0.1.0",
    description="Parallel FastAPI backend for trading dashboard services.",
)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "trading-dashboard-api", "docs": "/docs"}


app.include_router(health_router)
app.include_router(symbols_router)
app.include_router(analysis_router)
app.include_router(cockpit_router)
app.include_router(persistence_router)
