from __future__ import annotations

import tomllib
from pathlib import Path


def test_pyproject_uses_src_package_layout() -> None:
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert "build-system" in data
    assert data["tool"]["setuptools"]["package-dir"] == {"": "src"}
    assert data["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]
