from __future__ import annotations

import json
from typing import Any


FINITE_FIRST_MODULES = {
    "field_analysis.finite_first_phase_sync",
    "field_analysis.first_modeling_voltage_response",
    "field_analysis.modeling_error_metrics",
    "field_analysis.final_modeled_lut",
    "field_analysis.voltage_policy",
}

OPTIONAL_WORKFLOW_MODULES = {
    "field_analysis.finite_second_modeling",
    "field_analysis.continuous_steady_state_schema",
    "field_analysis.continuous_first_modeling",
}


def compact_runtime_diagnostic_packet(packet: dict[str, Any]) -> dict[str, Any]:
    module_status = packet.get("module_status") or {}
    helper_status = packet.get("helper_api_status") or {}
    return {
        "expected_core_repo": packet.get("expected_core_repo"),
        "expected_core_sha": packet.get("expected_core_sha"),
        "configured_core_path": packet.get("configured_core_path"),
        "configured_core_paths": packet.get("configured_core_paths") or [],
        "environment_core_src": packet.get("environment_core_src"),
        "added_sys_path": packet.get("added_sys_path"),
        "actual_core_sha": packet.get("actual_core_sha"),
        "actual_core_sha_matches_expected": packet.get("actual_core_sha_matches_expected"),
        "streamlit_imported": packet.get("streamlit_imported"),
        "forbidden_module_status": packet.get("forbidden_module_status") or {},
        "module_status_summary": _status_summary(module_status),
        "finite_first_api": packet.get("finite_first_api") or {},
        "helper_api_status_summary": _status_summary(helper_status),
        "missing_core_modules": _missing_modules(module_status),
        "missing_finite_first_modules": _missing_modules(module_status, FINITE_FIRST_MODULES),
        "missing_optional_workflow_modules": _missing_modules(module_status, OPTIONAL_WORKFLOW_MODULES),
    }


def format_runtime_diagnostic_packet(packet: dict[str, Any]) -> str:
    return json.dumps(compact_runtime_diagnostic_packet(packet), ensure_ascii=False, indent=2, sort_keys=True)


def build_core_status_summary(status_or_packet: dict[str, Any]) -> dict[str, Any]:
    forbidden = status_or_packet.get("forbidden_module_status") or {}
    forbidden_loaded = sorted(name for name, item in forbidden.items() if isinstance(item, dict) and item.get("loaded"))
    module_status = status_or_packet.get("module_status") or {}
    if "missing_finite_first_modules" in status_or_packet:
        missing_finite = list(status_or_packet.get("missing_finite_first_modules") or [])
    else:
        missing_finite = _missing_modules(module_status, FINITE_FIRST_MODULES)
    if "missing_optional_workflow_modules" in status_or_packet:
        missing_optional = list(status_or_packet.get("missing_optional_workflow_modules") or [])
    else:
        missing_optional = _missing_modules(module_status, OPTIONAL_WORKFLOW_MODULES)
    core_path_configured = bool(status_or_packet.get("core_path_configured") or status_or_packet.get("configured_core_path"))
    package_available = bool(
        status_or_packet.get("core_package_import_available")
        if "core_package_import_available" in status_or_packet
        else not _missing_field_analysis_package(status_or_packet.get("module_status") or {})
    )
    finite_api_available = bool(
        status_or_packet.get("finite_first_api_available")
        if "finite_first_api_available" in status_or_packet
        else (status_or_packet.get("finite_first_api") or {}).get("status") == "ok"
    )
    sha_match = status_or_packet.get("actual_core_sha_matches_expected")

    severity = "ok"
    headline = "Finite-first core is ready."
    blocking_reason: str | None = None
    if forbidden_loaded:
        severity = "error"
        blocking_reason = "forbidden module loaded: " + ", ".join(forbidden_loaded)
    elif not core_path_configured:
        severity = "error"
        blocking_reason = "core path is not configured"
    elif not package_available:
        severity = "error"
        blocking_reason = "field_analysis package is not importable"
    elif missing_finite:
        severity = "error"
        blocking_reason = "missing finite-first modules: " + ", ".join(missing_finite)
    elif not finite_api_available:
        severity = "error"
        blocking_reason = "finite-first API is unavailable"
    elif sha_match is False:
        severity = "error"
        blocking_reason = "actual core SHA does not match expected SHA"
    elif sha_match is None:
        severity = "warning"
        headline = "Finite-first core appears available, but core SHA is unknown."
    elif missing_optional:
        severity = "warning"
        headline = "Finite-first core is available; optional workflows remain unavailable."

    if blocking_reason:
        headline = "Finite-first core is blocked."

    return {
        "severity": severity,
        "headline": headline,
        "blocking_reason": blocking_reason,
        "core_path_configured": core_path_configured,
        "core_package_import_available": package_available,
        "finite_first_api_available": finite_api_available,
        "actual_core_sha_matches_expected": sha_match,
        "missing_finite_first_modules": missing_finite,
        "missing_optional_workflow_modules": missing_optional,
    }


def _status_summary(items: dict[str, Any]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for value in items.values():
        status = value.get("status", "unknown") if isinstance(value, dict) else "unknown"
        summary[status] = summary.get(status, 0) + 1
    return summary


def _missing_modules(module_status: dict[str, Any], names: set[str] | None = None) -> list[str]:
    missing: list[str] = []
    for module_name, value in module_status.items():
        if names is not None and module_name not in names:
            continue
        if isinstance(value, dict) and value.get("status") != "ok":
            missing.append(module_name)
    return sorted(missing)


def _missing_field_analysis_package(module_status: dict[str, Any]) -> bool:
    if not module_status:
        return True
    return all(isinstance(value, dict) and "No module named 'field_analysis'" in str(value.get("core_import_error", "")) for value in module_status.values())
