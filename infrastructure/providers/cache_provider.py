from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CacheItem:
    key: str
    payload: dict[str, Any]
    expires_at: datetime | None


class FileCacheProvider:
    def __init__(self, cache_dir: str | Path = "data/cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> dict[str, Any] | None:
        file_path = self._path_for_key(key)
        if not file_path.exists():
            return None

        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        expires_at = _parse_iso(payload.get("expires_at"))
        if expires_at is not None and datetime.now(timezone.utc) >= expires_at:
            try:
                file_path.unlink(missing_ok=True)
            except OSError:
                pass
            return None

        data = payload.get("data")
        return data if isinstance(data, dict) else None

    def set(self, key: str, data: dict[str, Any], ttl_seconds: int | None = None) -> CacheItem:
        expires_at = None
        if ttl_seconds is not None and ttl_seconds > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        item = {
            "key": key,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "data": data,
        }
        file_path = self._path_for_key(key)
        file_path.write_text(json.dumps(item, ensure_ascii=True), encoding="utf-8")
        return CacheItem(key=key, payload=data, expires_at=expires_at)

    def delete(self, key: str) -> None:
        try:
            self._path_for_key(key).unlink(missing_ok=True)
        except OSError:
            pass

    def clear(self) -> None:
        for file_path in self.cache_dir.glob("*.json"):
            try:
                file_path.unlink(missing_ok=True)
            except OSError:
                continue

    def _path_for_key(self, key: str) -> Path:
        normalized = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in key)
        return self.cache_dir / f"{normalized}.json"


def _parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

