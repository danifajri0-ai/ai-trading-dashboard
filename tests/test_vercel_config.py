from __future__ import annotations

import json
from pathlib import Path


def test_vercel_config_keeps_web_and_api_split() -> None:
    config_path = Path("vercel.json")
    assert config_path.exists(), "vercel.json harus tersedia di root project."

    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["experimentalServices"]["web"]["entrypoint"] == "apps/web"
    assert config["experimentalServices"]["api"]["entrypoint"] == "apps/api/vercel_entry.py"
    assert config["experimentalServices"]["web"]["routePrefix"] == "/"
    assert config["experimentalServices"]["api"]["routePrefix"] == "/backend"


def test_vercel_config_excludes_frontend_and_legacy_files_from_python_bundle() -> None:
    config = json.loads(Path("vercel.json").read_text(encoding="utf-8"))
    exclude_files = config["experimentalServices"]["api"]["excludeFiles"]

    for pattern in [
        "apps/web/**",
        "apps/streamlit_app/**",
        "docs/**",
        "tests/**",
        "research/**",
        "runtime/**",
        "venv/**",
        ".pytest_cache/**",
        "pytest_temp/**",
        "**/__pycache__/**",
        "**/*.pyc",
    ]:
        assert pattern in exclude_files
