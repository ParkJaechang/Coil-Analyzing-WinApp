from __future__ import annotations

import importlib
import inspect
import os
import subprocess
import sys
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

FINITE_FIRST_REQUIRED_MODULES = [
    "field_analysis.finite_first_phase_sync",
    "field_analysis.first_modeling_voltage_response",
    "field_analysis.modeling_error_metrics",
    "field_analysis.final_modeled_lut",
    "field_analysis.voltage_policy",
]

OPTIONAL_WORKFLOW_MODULES = [
    "field_analysis.finite_second_modeling",
    "field_analysis.continuous_steady_state_schema",
    "field_analysis.continuous_first_modeling",
]

FINITE_FIRST_API_MODULE = "field_analysis.finite_first_phase_sync"
FINITE_FIRST_API_NAME = "apply_finite_first_phase_sync_modeling"
HELPER_APIS = {
    "field_analysis.first_modeling_voltage_response.field_per_volt_response_metadata": (
        "field_analysis.first_modeling_voltage_response",
        "field_per_volt_response_metadata",
    ),
    "field_analysis.first_modeling_voltage_response.residual_to_voltage_delta_from_field_per_volt": (
        "field_analysis.first_modeling_voltage_response",
        "residual_to_voltage_delta_from_field_per_volt",
    ),
    "field_analysis.modeling_error_metrics.peak_error_metrics": (
        "field_analysis.modeling_error_metrics",
        "peak_error_metrics",
    ),
    "field_analysis.final_modeled_lut.build_final_modeled_voltage_lut_export": (
        "field_analysis.final_modeled_lut",
        "build_final_modeled_voltage_lut_export",
    ),
}

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
    _clear_field_analysis_modules()
    sys.path[:] = [entry for entry in sys.path if entry != import_path]
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
    finite_missing = [module for module in FINITE_FIRST_REQUIRED_MODULES if module in missing]
    optional_missing = [module for module in OPTIONAL_WORKFLOW_MODULES if module in missing]
    finite_api = _callable_status(FINITE_FIRST_API_MODULE, FINITE_FIRST_API_NAME)
    package_status = import_core_module("field_analysis")
    forbidden = _forbidden_module_status()
    blocked_forbidden = [name for name, item in forbidden.items() if item.get("loaded")]
    api_missing_reason = ""
    if package_status["status"] != "ok":
        api_missing_reason = package_status["core_import_error"]
    elif finite_missing:
        api_missing_reason = "missing finite first core modules"
    elif finite_api["status"] != "ok":
        api_missing_reason = finite_api["core_import_error"]
    elif blocked_forbidden:
        api_missing_reason = "forbidden module imported"

    configured_path = _CONFIGURED_CORE_PATHS[-1] if _CONFIGURED_CORE_PATHS else None
    actual_sha = _git_sha_for_configured_path(configured_path)
    return {
        "core_repo": CORE_REPO,
        "core_sha": CORE_SHA,
        "core_path_configured": bool(_CONFIGURED_CORE_PATHS),
        "core_package_import_available": package_status["status"] == "ok",
        "core_import_available": not errors,
        "core_import_error": "; ".join(errors),
        "core_modules_checked": checked,
        "missing_core_modules": missing,
        "missing_finite_first_modules": finite_missing,
        "missing_optional_workflow_modules": optional_missing,
        "finite_first_core_available": not finite_missing and package_status["status"] == "ok",
        "finite_first_api_available": finite_api["status"] == "ok",
        "required_core_api": f"{FINITE_FIRST_API_MODULE}.{FINITE_FIRST_API_NAME}",
        "api_missing_reason": api_missing_reason,
        "optional_core_modules_available": available,
        "configured_core_path": configured_path,
        "configured_core_paths": list(_CONFIGURED_CORE_PATHS),
        "added_sys_path": configured_path,
        "actual_core_sha": actual_sha,
        "actual_core_sha_matches_expected": None if actual_sha is None else actual_sha == CORE_SHA,
        "streamlit_imported": "streamlit" in sys.modules,
        "forbidden_module_status": forbidden,
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


def build_runtime_diagnostic_packet() -> dict[str, Any]:
    _configure_from_environment_once()
    module_status = {module_name: _module_status(module_name) for module_name in REQUIRED_CORE_MODULES}
    finite_first_api = _callable_status(FINITE_FIRST_API_MODULE, FINITE_FIRST_API_NAME)
    helper_api_status = {
        api_name: _callable_status(module_name, function_name)
        for api_name, (module_name, function_name) in HELPER_APIS.items()
    }
    configured_path = _CONFIGURED_CORE_PATHS[-1] if _CONFIGURED_CORE_PATHS else None
    actual_sha = _git_sha_for_configured_path(configured_path)
    return {
        "expected_core_repo": CORE_REPO,
        "expected_core_sha": CORE_SHA,
        "configured_core_path": configured_path,
        "configured_core_paths": list(_CONFIGURED_CORE_PATHS),
        "environment_core_src": os.environ.get("COIL_ANALYZING_CORE_SRC"),
        "added_sys_path": configured_path,
        "actual_core_sha": actual_sha,
        "actual_core_sha_matches_expected": None if actual_sha is None else actual_sha == CORE_SHA,
        "streamlit_imported": "streamlit" in sys.modules,
        "forbidden_module_status": _forbidden_module_status(),
        "module_status": module_status,
        "finite_first_api": finite_first_api,
        "helper_api_status": helper_api_status,
    }


def _failed_status(module_name: str, reason: str) -> dict[str, Any]:
    return {
        "status": "failed",
        "module_name": module_name,
        "module": None,
        "core_import_error": reason,
    }


def _module_status(module_name: str) -> dict[str, Any]:
    result = import_core_module(module_name)
    module = result.get("module")
    return {
        "status": result["status"],
        "module_name": module_name,
        "module_file": getattr(module, "__file__", None) if module is not None else None,
        "core_import_error": result["core_import_error"],
    }


def _callable_status(module_name: str, function_name: str) -> dict[str, Any]:
    result = import_core_module(module_name)
    module = result.get("module")
    if result["status"] != "ok" or module is None:
        return {
            "status": "failed",
            "module_name": module_name,
            "function_name": function_name,
            "module_file": None,
            "signature": None,
            "core_import_error": result["core_import_error"],
        }
    function = getattr(module, function_name, None)
    if function is None or not callable(function):
        return {
            "status": "failed",
            "module_name": module_name,
            "function_name": function_name,
            "module_file": getattr(module, "__file__", None),
            "signature": None,
            "core_import_error": f"callable not found: {function_name}",
        }
    try:
        signature = str(inspect.signature(function))
    except Exception as exc:
        signature = f"unavailable: {exc}"
    return {
        "status": "ok",
        "module_name": module_name,
        "function_name": function_name,
        "module_file": getattr(module, "__file__", None),
        "signature": signature,
        "core_import_error": "",
    }


def _forbidden_module_status() -> dict[str, dict[str, Any]]:
    return {
        module_name: {
            "loaded": module_name in sys.modules,
            "module_file": getattr(sys.modules.get(module_name), "__file__", None),
        }
        for module_name in sorted(FORBIDDEN_CORE_MODULES)
    }


def _clear_field_analysis_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "field_analysis" or module_name.startswith("field_analysis."):
            sys.modules.pop(module_name, None)


def _git_sha_for_configured_path(configured_path: str | None) -> str | None:
    if not configured_path:
        return None
    path = Path(configured_path)
    candidates = [path]
    if path.name.lower() == "src":
        candidates.append(path.parent)
    for candidate in candidates:
        if not (candidate / ".git").exists():
            continue
        try:
            completed = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(candidate),
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            continue
        return completed.stdout.strip() or None
    return None


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
