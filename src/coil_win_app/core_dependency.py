from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any

from coil_win_app.core_adapter import CORE_REPO, CORE_SHA


REQUIRED_CORE_MODULES = [
    "field_analysis.final_modeled_lut",
    "field_analysis.finite_first_phase_sync",
    "field_analysis.finite_second_modeling",
    "field_analysis.continuous_steady_state_schema",
    "field_analysis.continuous_first_modeling",
    "field_analysis.voltage_policy",
]

FORBIDDEN_CORE_MODULES = {
    "streamlit",
    "field_analysis.app_ui_snapshot",
}


def resolve_core_dependency() -> dict[str, Any]:
    checked: list[str] = []
    errors: list[str] = []
    for module_name in REQUIRED_CORE_MODULES:
        checked.append(module_name)
        result = import_core_module(module_name)
        if result["status"] != "ok":
            errors.append(f"{module_name}: {result['core_import_error']}")
    return {
        "core_repo": CORE_REPO,
        "core_sha": CORE_SHA,
        "core_import_available": not errors,
        "core_import_error": "; ".join(errors),
        "core_modules_checked": checked,
    }


def get_core_dependency_status() -> dict[str, Any]:
    return resolve_core_dependency()


def import_core_module(module_name: str) -> dict[str, Any]:
    if module_name in FORBIDDEN_CORE_MODULES or module_name.startswith("streamlit"):
        return _failed_status(module_name, "forbidden core module")
    try:
        before_streamlit = "streamlit" in sys.modules
        module = importlib.import_module(module_name)
        if "streamlit" in sys.modules and not before_streamlit:
            sys.modules.pop("streamlit", None)
            return _failed_status(module_name, "core module imported streamlit")
    except Exception as exc:
        return _failed_status(module_name, str(exc))
    return {
        "status": "ok",
        "module_name": module_name,
        "module": module,
        "core_import_error": "",
    }


def _failed_status(module_name: str, reason: str) -> dict[str, Any]:
    return {
        "status": "failed",
        "module_name": module_name,
        "module": None,
        "core_import_error": reason,
    }
