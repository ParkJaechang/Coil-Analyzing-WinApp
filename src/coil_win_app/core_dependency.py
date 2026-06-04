from __future__ import annotations

import importlib
import os
import sys
from types import ModuleType
from pathlib import Path
from typing import Any

from coil_win_app.core_adapter import CORE_REPO, CORE_SHA


REQUIRED_CORE_MODULES = [
    "field_analysis.final_modeled_lut",
    "field_analysis.finite_first_phase_sync",
    "field_analysis.first_modeling_voltage_response",
    "field_analysis.modeling_error_metrics",
    "field_analysis.finite_second_modeling",
    "field_analysis.continuous_steady_state_schema",
    "field_analysis.continuous_first_modeling",
    "field_analysis.voltage_policy",
]

FORBIDDEN_CORE_MODULES = {
    "streamlit",
    "field_analysis.app_ui_snapshot",
}

_CONFIGURED_CORE_PATHS: list[str] = []


def configure_core_path(path: str | Path) -> dict[str, Any]:
    candidate = Path(path).expanduser()
    if not candidate.exists():
        return _failed_status("core_path", f"core path does not exist: {candidate}") | {
            "configured_core_path": None,
            "added_sys_path": None,
        }
    import_root = _resolve_import_root(candidate)
    if import_root is None:
        return _failed_status("core_path", f"field_analysis package was not found under: {candidate}") | {
            "configured_core_path": None,
            "added_sys_path": None,
        }
    import_path = str(import_root)
    if import_path not in sys.path:
        sys.path.insert(0, import_path)
    importlib.invalidate_caches()
    if import_path not in _CONFIGURED_CORE_PATHS:
        _CONFIGURED_CORE_PATHS.append(import_path)
    return {
        "status": "ok",
        "module_name": "core_path",
        "module": None,
        "core_import_error": "",
        "configured_core_path": import_path,
        "added_sys_path": import_path,
    }


def get_configured_core_paths() -> list[str]:
    return list(_CONFIGURED_CORE_PATHS)


def resolve_core_dependency() -> dict[str, Any]:
    _configure_from_environment_once()
    checked: list[str] = []
    errors: list[str] = []
    available: list[str] = []
    missing: list[str] = []
    for module_name in REQUIRED_CORE_MODULES:
        checked.append(module_name)
        result = import_core_module(module_name)
        if result["status"] != "ok":
            errors.append(f"{module_name}: {result['core_import_error']}")
            missing.append(module_name)
        else:
            available.append(module_name)
    return {
        "core_repo": CORE_REPO,
        "core_sha": CORE_SHA,
        "core_import_available": not errors,
        "core_import_error": "; ".join(errors),
        "core_modules_checked": checked,
        "missing_core_modules": missing,
        "optional_core_modules_available": available,
        "configured_core_path": _CONFIGURED_CORE_PATHS[-1] if _CONFIGURED_CORE_PATHS else None,
        "configured_core_paths": list(_CONFIGURED_CORE_PATHS),
        "added_sys_path": _CONFIGURED_CORE_PATHS[-1] if _CONFIGURED_CORE_PATHS else None,
        "streamlit_imported": "streamlit" in sys.modules,
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


def _configure_from_environment_once() -> None:
    if _CONFIGURED_CORE_PATHS:
        return
    env_path = os.environ.get("COIL_ANALYZING_CORE_SRC")
    if env_path:
        configure_core_path(env_path)


def _resolve_import_root(candidate: Path) -> Path | None:
    if (candidate / "field_analysis" / "__init__.py").is_file():
        return candidate
    if (candidate / "src" / "field_analysis" / "__init__.py").is_file():
        return candidate / "src"
    if candidate.name.lower() == "src" and (candidate / "field_analysis").is_dir():
        return candidate
    if (candidate / "field_analysis").is_dir():
        return candidate
    return None
