from __future__ import annotations

from pathlib import Path


def test_domain_package_does_not_import_streamlit() -> None:
    domain_dir = Path("domain")
    assert domain_dir.exists(), "domain directory must exist"

    for file_path in domain_dir.rglob("*.py"):
        content = file_path.read_text(encoding="utf-8")
        assert "import streamlit" not in content, f"Streamlit import found in {file_path}"
        assert "from streamlit" not in content, f"Streamlit import found in {file_path}"


def test_runtime_layers_do_not_depend_on_root_compatibility_modules() -> None:
    runtime_dirs = (Path("services"), Path("infrastructure"))
    forbidden_imports = (
        "from market_data import",
        "import market_data",
        "from ai_signal import",
        "import ai_signal",
        "from sentiment_news import",
        "import sentiment_news",
        "from technical_analysis import",
        "import technical_analysis",
    )

    for runtime_dir in runtime_dirs:
        for file_path in runtime_dir.rglob("*.py"):
            content = file_path.read_text(encoding="utf-8")
            for forbidden_import in forbidden_imports:
                assert forbidden_import not in content, (
                    f"Compatibility import '{forbidden_import}' found in {file_path}"
                )
