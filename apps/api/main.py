from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routes import analysis_router, cockpit_router, health_router, persistence_router, symbols_router
from config import SETTINGS


app = FastAPI(
    title="Trading Dashboard API",
    version="0.1.0",
    description="Parallel FastAPI backend for trading dashboard services.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(SETTINGS.allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "trading-dashboard-api", "docs": "/docs"}


app.include_router(health_router)
app.include_router(symbols_router)
app.include_router(analysis_router)
app.include_router(cockpit_router)
app.include_router(persistence_router)
