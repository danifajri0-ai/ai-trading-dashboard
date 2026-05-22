from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8000"


def _get(path: str) -> dict:
    url = f"{BASE_URL}{path}"
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _post(path: str, payload: dict) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def run() -> None:
    try:
        print("GET /health")
        print(_get("/health"))
        print("\nGET /symbols")
        print(_get("/symbols"))
        print("\nPOST /analyze")
        print(_post("/analyze", {"symbol": "BTCUSD", "timeframe": "H1"}))
    except HTTPError as exc:
        print(f"HTTP error: {exc.code} {exc.reason}")
        try:
            print(exc.read().decode("utf-8"))
        except Exception:
            pass
    except URLError as exc:
        print(f"Connection error: {exc.reason}")


if __name__ == "__main__":
    run()

