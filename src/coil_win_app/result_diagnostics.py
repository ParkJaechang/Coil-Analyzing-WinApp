from __future__ import annotations

from typing import Any

import pandas as pd

from coil_win_app.core_adapter import ModelingResult


REQUIRED_EXPORT_COLUMNS = ["time_s", "limited_voltage_v"]
EXPORT_COLUMNS = ["sample_index", "time_s", "voltage_v"]


def explain_final_lut_export_eligibility(
    result: ModelingResult,
    *,
    allow_demo: bool = False,
    allow_non_monotonic_time: bool = False,
) -> dict[str, Any]:
    profile = result.command_profile
    actual_columns = [str(column) for column in profile.columns] if profile is not None else []
    time_nonfinite = False
    voltage_nonfinite = False
    time_monotonic = None
    if profile is not None and "time_s" in profile.columns:
        time_s = pd.to_numeric(profile["time_s"], errors="coerce")
        time_nonfinite = not _series_all_finite(time_s)
        time_monotonic = bool(time_s.is_monotonic_increasing)
    if profile is not None and "limited_voltage_v" in profile.columns:
        voltage_v = pd.to_numeric(profile["limited_voltage_v"], errors="coerce")
        voltage_nonfinite = not _series_all_finite(voltage_v)

    base = {
        "result_status": result.status,
        "result_kind": result.metadata.get("result_kind"),
        "demo_only": bool(result.metadata.get("demo_only")),
        "finite_first_modeling_status": result.metadata.get("finite_first_modeling_status"),
        "required_columns": list(REQUIRED_EXPORT_COLUMNS),
        "actual_columns": actual_columns,
        "command_profile_present": profile is not None,
        "command_profile_empty": bool(profile is not None and profile.empty),
        "nonfinite_time_or_voltage": bool(time_nonfinite or voltage_nonfinite),
        "time_monotonic": time_monotonic,
        "export_columns": None,
    }

    if result.status != "ok":
        return _blocked(base, f"modeling result status is not ok: {result.status}")
    if result.metadata.get("result_kind") in {"source_preview", "source_dataframe"}:
        return _blocked(base, "source preview/dataframe is not a final LUT export candidate")
    if result.metadata.get("demo_only") and not allow_demo:
        return _blocked(base, "demo modeling result requires explicit demo export path")
    finite_status = result.metadata.get("finite_first_modeling_status")
    if finite_status is not None and finite_status != "ok":
        return _blocked(base, f"finite first modeling status is not ok: {finite_status}")
    if profile is None:
        return _blocked(base, "command_profile is missing")
    if profile.empty:
        return _blocked(base, "command_profile is empty")
    missing = [column for column in REQUIRED_EXPORT_COLUMNS if column not in profile.columns]
    if missing:
        return _blocked(base, f"command_profile missing required columns: {', '.join(missing)}")
    if base["nonfinite_time_or_voltage"]:
        return _blocked(base, "command_profile contains non-finite time_s or limited_voltage_v values")
    if not allow_non_monotonic_time and not time_monotonic:
        return _blocked(base, "command_profile time_s is non-monotonic")
    return {"eligible": True, "blocking_reason": None, **base, "export_columns": list(EXPORT_COLUMNS)}


def summarize_finite_first_result(result: ModelingResult) -> dict[str, Any]:
    profile = result.command_profile
    schema = result.metadata.get("finite_first_input_schema") or {
        "status": result.metadata.get("finite_first_input_schema_status"),
        "resolved_columns": result.metadata.get("resolved_columns", {}),
        "missing_column_groups": result.metadata.get("missing_column_groups", []),
        "prepared_columns": result.metadata.get("prepared_columns", []),
    }
    eligibility = explain_final_lut_export_eligibility(result)
    target_config = result.metadata.get("target_config", {})
    return {
        "status": result.status,
        "error_reason": result.error_reason,
        "selected_source_filename": result.metadata.get("selected_source_filename"),
        "selected_source_category": result.metadata.get("selected_source_category"),
        "selected_source_path": result.metadata.get("selected_source_path"),
        "required_core_api": result.metadata.get("required_core_api"),
        "target_config": {
            "freq_hz": target_config.get("freq_hz"),
            "cycle_count": target_config.get("cycle_count"),
            "target_peak_field_mT": target_config.get("target_peak_field_mT"),
            "voltage_limit_v": target_config.get("voltage_limit_v"),
        },
        "finite_first_modeling_status": result.metadata.get("finite_first_modeling_status"),
        "core_bridge_used": result.metadata.get("core_bridge_used"),
        "finite_first_bridge_version": result.metadata.get("finite_first_bridge_version"),
        "finite_first_input_schema": {
            "status": schema.get("status"),
            "resolved_columns": schema.get("resolved_columns", {}),
            "missing_column_groups": schema.get("missing_column_groups", []),
            "prepared_columns": schema.get("prepared_columns", []),
        },
        "command_profile_present": profile is not None,
        "command_profile_row_count": 0 if profile is None else int(len(profile)),
        "command_profile_columns": [] if profile is None else [str(column) for column in profile.columns],
        "has_time_s": bool(profile is not None and "time_s" in profile.columns),
        "has_limited_voltage_v": bool(profile is not None and "limited_voltage_v" in profile.columns),
        "limited_voltage_v_peak": _limited_voltage_peak(profile),
        "final_voltage_limit_v": result.metadata.get("final_voltage_limit_v"),
        "field_per_volt_mT_per_v": result.metadata.get("field_per_volt_mT_per_v"),
        "voltage_per_field_v_per_mT": result.metadata.get("voltage_per_field_v_per_mT"),
        "residual_to_voltage_conversion_basis": result.metadata.get("residual_to_voltage_conversion_basis"),
        "correction_delta_mode": result.metadata.get("correction_delta_mode"),
        "clipping_fraction": result.metadata.get("clipping_fraction"),
        "phase_sync_method": result.metadata.get("phase_sync_method"),
        "phase_sync_alignment_anchor": result.metadata.get("phase_sync_alignment_anchor"),
        "phase_sync_peak_reference": result.metadata.get("phase_sync_peak_reference"),
        "phase_delay_s": result.metadata.get("phase_delay_s"),
        "phase_delay_cycles": result.metadata.get("phase_delay_cycles"),
        "error_evaluation_start_cycle": result.metadata.get("error_evaluation_start_cycle"),
        "error_evaluation_end_cycle": result.metadata.get("error_evaluation_end_cycle"),
        "error_evaluation_finite_ratio": result.metadata.get("error_evaluation_finite_ratio"),
        "positive_peak_error_ratio": result.metadata.get("positive_peak_error_ratio"),
        "negative_peak_error_ratio": result.metadata.get("negative_peak_error_ratio"),
        "peak_to_peak_error_ratio": result.metadata.get("peak_to_peak_error_ratio"),
        "final_export_candidate": eligibility["eligible"],
        "final_export_blocking_reason": eligibility["blocking_reason"],
    }


def format_finite_first_summary(result: ModelingResult) -> str:
    summary = summarize_finite_first_result(result)
    lines = ["finite first run summary:"]
    for key, value in summary.items():
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def _blocked(base: dict[str, Any], reason: str) -> dict[str, Any]:
    return {"eligible": False, "blocking_reason": reason, **base}


def _limited_voltage_peak(profile: pd.DataFrame | None) -> float | None:
    if profile is None or "limited_voltage_v" not in profile.columns:
        return None
    values = pd.to_numeric(profile["limited_voltage_v"], errors="coerce").abs()
    values = values[_series_finite_mask(values)]
    if values.empty:
        return None
    return float(values.max())


def _series_all_finite(series: pd.Series) -> bool:
    numeric = pd.to_numeric(series, errors="coerce")
    return bool(_series_finite_mask(numeric).all())


def _series_finite_mask(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.notna() & (numeric != float("inf")) & (numeric != float("-inf"))
