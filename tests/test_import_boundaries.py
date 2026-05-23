from __future__ import annotations

from pathlib import Path


def test_domain_package_does_not_import_streamlit() -> None:
    domain_dir = Path("domain")
    assert domain_dir.exists(), "domain directory must exist"

    for file_path in domain_dir.rglob("*.py"):
        content = file_path.read_text(encoding="utf-8")
        assert "import streamlit" not in content, f"Streamlit import found in {file_path}"
        assert "from streamlit" not in content, f"Streamlit import found in {file_path}"
