from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    market_cache: Path
    cockpit: Path
    signal_history: Path
    cockpit_db: Path


def build_runtime_paths(project_root: Path = PROJECT_ROOT) -> RuntimePaths:
    root = _resolve_runtime_root(project_root)
    cockpit_dir = root / "cockpit"
    return RuntimePaths(
        root=root,
        market_cache=root / "market_cache",
        cockpit=cockpit_dir,
        signal_history=cockpit_dir / "signal_history.jsonl",
        cockpit_db=cockpit_dir / "cockpit.db",
    )


def _resolve_runtime_root(project_root: Path) -> Path:
    explicit_runtime_dir = os.getenv("TRADING_DASHBOARD_RUNTIME_DIR")
    if explicit_runtime_dir:
        return Path(explicit_runtime_dir).expanduser().resolve()

    if _is_vercel_runtime():
        return Path(tempfile.gettempdir()) / "ai_trading_dashboard_runtime"

    return project_root / "runtime"


def _is_vercel_runtime() -> bool:
    vercel_markers = (
        os.getenv("VERCEL"),
        os.getenv("VERCEL_ENV"),
        os.getenv("VERCEL_URL"),
        os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
    )
    return any(bool(marker) for marker in vercel_markers)


RUNTIME_PATHS = build_runtime_paths()
