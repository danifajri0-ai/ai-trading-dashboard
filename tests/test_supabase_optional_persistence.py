from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app
from infrastructure.storage.supabase_client import build_supabase_client


def test_supabase_client_defaults_to_disabled_mode_without_env() -> None:
    client = build_supabase_client()

    assert client.enabled is False
    assert client.reason is not None


def test_health_endpoint_remains_available_when_supabase_disabled() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_persistence_endpoints_return_clear_response_when_supabase_disabled() -> None:
    client = TestClient(app)

    post_log = client.post(
        "/api/analysis/logs",
        json={
            "symbol": "BTCUSD",
            "timeframe": "H1",
            "signal": "BUY",
            "bias": "BULLISH",
            "confidence": 70.0,
            "summary": "test",
            "raw_payload": {},
        },
    )
    get_history = client.get("/api/analysis/history")
    post_watchlist = client.post(
        "/api/watchlist",
        json={"symbol": "BTCUSD", "market_type": "crypto", "notes": "test"},
    )
    get_watchlist = client.get("/api/watchlist")
    delete_watchlist = client.delete("/api/watchlist/123")

    for response in (post_log, get_history, post_watchlist, get_watchlist, delete_watchlist):
        assert response.status_code == 503
        detail = str(response.json().get("detail", "")).lower()
        assert "supabase" in detail


def test_analyze_endpoint_still_works_with_save_to_history_flag_when_supabase_disabled() -> None:
    client = TestClient(app)

    response = client.post("/analyze", json={"symbol": "BTCUSD", "timeframe": "H1", "save_to_history": True})

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "BTCUSD"
    assert payload["timeframe"] == "H1"
    assert "signal" in payload
