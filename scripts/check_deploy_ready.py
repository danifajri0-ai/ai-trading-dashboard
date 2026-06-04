from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]


def _read_env_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    for line in _read_lines(path):
        if "=" not in line:
            continue
        key, _ = line.split("=", 1)
        key = key.strip()
        if key:
            keys.add(key)
    return keys


def _require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []

    vercel_path = ROOT / "vercel.json"
    requirements_path = ROOT / "requirements.txt"
    requirements_local_path = ROOT / "requirements-local.txt"
    requirements_api_local_path = ROOT / "requirements-api-local.txt"
    env_example_path = ROOT / ".env.example"
    env_local_path = ROOT / ".env.local"
    gitignore_path = ROOT / ".gitignore"
    vercelignore_path = ROOT / ".vercelignore"

    _require(vercel_path.exists(), "vercel.json is missing.", failures)
    _require(requirements_path.exists(), "requirements.txt is missing.", failures)
    _require(requirements_local_path.exists(), "requirements-local.txt is missing.", failures)
    _require(requirements_api_local_path.exists(), "requirements-api-local.txt is missing.", failures)
    _require(env_example_path.exists(), ".env.example is missing.", failures)
    _require(env_local_path.exists(), ".env.local is missing.", failures)
    _require(gitignore_path.exists(), ".gitignore is missing.", failures)
    _require(vercelignore_path.exists(), ".vercelignore is missing.", failures)

    if vercel_path.exists():
        config = json.loads(vercel_path.read_text(encoding="utf-8"))
        services = config.get("experimentalServices", {})
        web = services.get("web", {})
        api = services.get("api", {})

        _require(web.get("entrypoint") == "apps/web", "Vercel web entrypoint must be apps/web.", failures)
        _require(web.get("routePrefix") == "/", "Vercel web route prefix must be '/'.", failures)
        _require(api.get("entrypoint") == "apps/api/vercel_entry.py", "Vercel api entrypoint must be apps/api/vercel_entry.py.", failures)
        _require(api.get("routePrefix") == "/backend", "Vercel api route prefix must be '/backend'.", failures)

        functions = config.get("functions", {})
        api_bundle = functions.get("apps/api/**/*.py", {})
        exclude_files = api_bundle.get("excludeFiles", "")
        for pattern in [
            "apps/web/**",
            "apps/streamlit_app/**",
            "docs/**",
            "tests/**",
            "research/**",
            "runtime/**",
            "venv/**",
        ]:
            _require(pattern in exclude_files, f"vercel.json excludeFiles should include {pattern}.", failures)

    if requirements_path.exists():
        requirements = set(_read_lines(requirements_path))
        for forbidden in ["streamlit", "streamlit-autorefresh", "plotly", "uvicorn", "python-dotenv"]:
            _require(all(not line.startswith(forbidden) for line in requirements), f"requirements.txt should not include {forbidden}.", failures)

    if requirements_local_path.exists():
        local_requirements = set(_read_lines(requirements_local_path))
        for expected in ["streamlit", "streamlit-autorefresh", "plotly"]:
            _require(any(line.startswith(expected) for line in local_requirements), f"requirements-local.txt should include {expected}.", failures)

    if requirements_api_local_path.exists():
        api_local_requirements = set(_read_lines(requirements_api_local_path))
        _require(any(line.startswith("uvicorn") for line in api_local_requirements), "requirements-api-local.txt should include uvicorn.", failures)

    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        _require(".env.local" in gitignore_content, ".gitignore should ignore .env.local.", failures)

    if vercelignore_path.exists():
        vercelignore_content = vercelignore_path.read_text(encoding="utf-8")
        for pattern in ["tests/**", "docs/**", "apps/streamlit_app/**", "runtime/**"]:
            _require(pattern in vercelignore_content, f".vercelignore should ignore {pattern}.", failures)

    if env_example_path.exists() and env_local_path.exists():
        example_keys = _read_env_keys(env_example_path)
        local_keys = _read_env_keys(env_local_path)
        missing_keys = sorted(example_keys - local_keys)
        _require(not missing_keys, f".env.local is missing keys from .env.example: {', '.join(missing_keys)}", failures)

    if failures:
        print("Deploy readiness check failed:\n")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Deploy readiness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
