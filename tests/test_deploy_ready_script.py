from __future__ import annotations

from pathlib import Path


def test_deploy_ready_script_checks_services_and_requirements() -> None:
    script_path = Path("scripts/check_deploy_ready.py")
    assert script_path.exists(), "scripts/check_deploy_ready.py harus tersedia."

    content = script_path.read_text(encoding="utf-8").lower()

    for needle in [
        "apps/web",
        "apps/api/vercel_entry.py",
        "requirements-local.txt",
        "requirements-api-local.txt",
        ".env.example",
        ".env.local",
        ".gitignore",
        ".vercelignore",
        "missing keys from .env.example",
        ".gitignore should ignore .env.local",
        "vercelignore_content",
        "tests/**",
        "docs/**",
        "streamlit-autorefresh",
        "uvicorn",
    ]:
        assert needle in content
