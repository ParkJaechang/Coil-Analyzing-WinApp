from __future__ import annotations

import sys


def test_core_dependency_resolver_returns_structured_status() -> None:
    from coil_win_app.core_dependency import REQUIRED_CORE_MODULES, get_core_dependency_status

    status = get_core_dependency_status()

    assert status["core_repo"] == "ParkJaechang/Coil-Analyzing"
    assert status["core_sha"]
    assert isinstance(status["core_import_available"], bool)
    assert isinstance(status["core_import_error"], str)
    assert status["core_modules_checked"] == REQUIRED_CORE_MODULES


def test_core_dependency_resolver_does_not_import_streamlit() -> None:
    from coil_win_app.core_dependency import get_core_dependency_status

    sys.modules.pop("streamlit", None)
    get_core_dependency_status()

    assert "streamlit" not in sys.modules


def test_import_core_module_failure_returns_status_not_exception() -> None:
    from coil_win_app.core_dependency import import_core_module

    result = import_core_module("field_analysis.module_that_does_not_exist")

    assert result["status"] == "failed"
    assert result["module_name"] == "field_analysis.module_that_does_not_exist"
    assert result["core_import_error"]
