from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_winapp_source_does_not_import_streamlit() -> None:
    offenders: list[str] = []
    for path in (REPO_ROOT / "src" / "coil_win_app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name == "streamlit" or alias.name.startswith("streamlit.") for alias in node.names):
                    offenders.append(path.as_posix())
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "streamlit" or module.startswith("streamlit."):
                    offenders.append(path.as_posix())
    assert offenders == []


def test_required_page_modules_exist() -> None:
    required = [
        "project_page.py",
        "target_config_page.py",
        "finite_modeling_page.py",
        "continuous_modeling_page.py",
        "final_export_page.py",
    ]
    ui_dir = REPO_ROOT / "src" / "coil_win_app" / "ui"
    for name in required:
        assert (ui_dir / name).exists()
