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
        "expected_core_sha": packet.get("expected_core_sha"),
        "actual_core_sha": packet.get("actual_core_sha"),
        "actual_core_sha_matches_expected": packet.get("actual_core_sha_matches_expected"),
        "configured_core_path": packet.get("configured_core_path"),
        "environment_core_src": packet.get("environment_core_src"),
        "streamlit_imported": packet.get("streamlit_imported"),
        "forbidden_module_status": packet.get("forbidden_module_status") or {},
        "finite_first_api": packet.get("finite_first_api") or {},
        "helper_api_status_summary": _status_summary(helper_status),
        "missing_core_modules": _missing_modules(module_status),
        "missing_finite_first_modules": _missing_modules(module_status, FINITE_FIRST_MODULES),
        "missing_optional_workflow_modules": _missing_modules(module_status, OPTIONAL_WORKFLOW_MODULES),
    }


def format_runtime_diagnostic_packet(packet: dict[str, Any]) -> str:
    return json.dumps(compact_runtime_diagnostic_packet(packet), ensure_ascii=False, indent=2, sort_keys=True)


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
