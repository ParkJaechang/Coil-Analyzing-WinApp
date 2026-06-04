from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

import pandas as pd


FINITE_PRODUCTION_CYCLES = (1.0, 1.5)
CONTINUOUS_CYCLE_COUNT = 1.0
TARGET_SHAPE = "fixed_rounded_triangle"
FIELD_NORMALIZATION_MODE = "target_peak"
VOLTAGE_LIMIT_V = 10.0
CORE_REPO = "ParkJaechang/Coil-Analyzing"
CORE_SHA = "a24d0388ca8d0be0e6a603df62936a3ff956a036"
FINITE_FIRST_REQUIRED_API = "field_analysis.finite_first_phase_sync.apply_finite_first_phase_sync_modeling"

ModelingMode = Literal["finite_startup_aware", "continuous_steady_state"]


@dataclass(frozen=True)
class TargetConfig:
    modeling_input_mode: ModelingMode
    freq_hz: float
    cycle_count: float
    target_peak_field_mT: float
    source_waveform_family: str = "sine"
    target_shape: str = TARGET_SHAPE
    field_normalization_mode: str = FIELD_NORMALIZATION_MODE
    voltage_limit_v: float = VOLTAGE_LIMIT_V
    finite_tail_mode: str | None = None
    continuous_loop_output: bool | None = None
    source_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelingResult:
    status: str
    metadata: dict[str, Any]
    warnings: list[str]
    command_profile: pd.DataFrame | None = None
    export_frame: pd.DataFrame | None = None
    error_reason: str | None = None


def get_core_version() -> dict[str, str]:
    try:
        from coil_win_app.core_dependency import get_core_dependency_status

        dependency = get_core_dependency_status()
        import_available = str(dependency["core_import_available"])
    except Exception as exc:
        import_available = f"False ({exc})"
    return {
        "core_repo": CORE_REPO,
        "core_sha": CORE_SHA,
        "adapter_status": "placeholder_not_connected",
        "core_import_available": import_available,
    }


def finite_first_required_metadata_keys() -> list[str]:
    return [
        "finite_first_modeling_status",
        "phase_sync_method",
        "phase_delay_s",
        "measured_field_scale_to_target_mT",
        "field_per_volt_mT_per_v",
        "residual_to_voltage_conversion_basis",
        "final_voltage_limit_v",
    ]


def finite_first_optional_metadata_keys() -> list[str]:
    return [
        "phase_sync_alignment_anchor",
        "phase_sync_midpoint_time_s",
        "phase_sync_target_zero_crossing_time_s",
        "error_evaluation_start_cycle",
        "error_evaluation_end_cycle",
        "error_evaluation_finite_ratio",
        "positive_peak_error_ratio",
        "negative_peak_error_ratio",
        "peak_to_peak_error_ratio",
    ]


def load_project_sources(project_path: str | Path) -> ModelingResult:
    root = Path(project_path).expanduser()
    if not root.exists():
        return _not_connected(f"project path does not exist: {root}")
    records = _scan_source_records(root)
    counts = _count_source_records(records)
    return ModelingResult(
        status="ok",
        metadata={"project_path": str(root), "source_counts": counts, "source_records": records},
        warnings=["core adapter is not connected; source scan is filesystem-only"],
    )


def read_source_dataframe(source_record: dict[str, Any]) -> ModelingResult:
    if not source_record or not source_record.get("path"):
        return _missing_source("source path is missing", None, "read_source_dataframe")
    path = Path(str(source_record["path"]))
    if path.suffix.lower() != ".csv":
        return _failed(f"unsupported file type for CSV source: {path.suffix or '<none>'}")
    if not path.exists():
        return _failed(f"source file does not exist: {path}")
    size = path.stat().st_size
    if size > 20_000_000:
        return _failed(f"source file is too large for CSV read: {size} bytes")
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        return _failed(f"CSV read failed: {exc}")
    return ModelingResult(
        status="ok",
        metadata={
            "result_kind": "source_dataframe",
            "filename": source_record.get("filename", path.name),
            "category": source_record.get("category", "unknown"),
            "path": str(path),
            "row_count": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "file_size_bytes": int(size),
        },
        warnings=[],
        command_profile=frame,
    )


def preview_source_file(source_record: dict[str, Any], max_rows: int = 20) -> ModelingResult:
    source = read_source_dataframe(source_record)
    if source.status != "ok" or source.command_profile is None:
        return source
    preview = source.command_profile.head(max_rows).copy()
    return ModelingResult(
        status="ok",
        metadata={
            "result_kind": "source_preview",
            "source_filename": source.metadata["filename"],
            "source_category": source.metadata["category"],
            "row_count_estimate": source.metadata["row_count"],
            "columns": source.metadata["columns"],
            "preview_row_count": int(len(preview)),
            "file_size_bytes": source.metadata["file_size_bytes"],
        },
        warnings=[],
        export_frame=preview,
    )


def validate_finite_first_input_frame(frame: pd.DataFrame) -> dict[str, Any]:
    candidates = {
        "time": ["time_s", "TimeMs"],
        "voltage": [
            "limited_voltage_v",
            "voltage_v",
            "command_voltage_v",
            "Voltage1_V",
            "raw_voltage_v",
            "finite_first_input_lut_voltage_v",
        ],
        "measured_field": [
            "finite_first_actual_measured_field_mT",
            "measured_field_effective_mT",
            "measured_field_normalized_mT",
            "raw_hallbz_mT",
            "HallBz",
            "HallZ",
            "bz_mT",
            "Bz_mT",
        ],
        "target_field": [
            "physical_target_output_mT",
            "target_field_mT",
            "normalized_physical_target_output_mT",
            "aligned_target_output",
        ],
    }
    resolved: dict[str, str] = {}
    missing: list[str] = []
    columns = {str(column) for column in frame.columns}
    for group, names in candidates.items():
        found = next((name for name in names if name in columns), None)
        if found is None:
            missing.append(group)
        else:
            resolved[group] = found
    return {
        "status": "ok" if not missing else "schema_unavailable",
        "resolved_columns": resolved,
        "missing_column_groups": missing,
        "required_column_candidates": candidates,
    }


def build_target_config(
    *,
    modeling_input_mode: ModelingMode,
    freq_hz: float,
    cycle_count: float,
    target_peak_field_mT: float,
    source_waveform_family: str = "sine",
    finite_tail_mode: str | None = "off",
    continuous_loop_output: bool | None = True,
    source_metadata: dict[str, Any] | None = None,
) -> TargetConfig:
    mode = str(modeling_input_mode)
    if mode == "finite_startup_aware":
        normalized_cycle = float(cycle_count)
        if normalized_cycle not in FINITE_PRODUCTION_CYCLES:
            raise ValueError(f"finite production cycles are {FINITE_PRODUCTION_CYCLES}")
    elif mode == "continuous_steady_state":
        normalized_cycle = CONTINUOUS_CYCLE_COUNT
        finite_tail_mode = None
        continuous_loop_output = True
    else:
        raise ValueError(f"unsupported modeling_input_mode: {modeling_input_mode}")
    return TargetConfig(
        modeling_input_mode=mode,  # type: ignore[arg-type]
        freq_hz=float(freq_hz),
        cycle_count=normalized_cycle,
        target_peak_field_mT=float(target_peak_field_mT),
        source_waveform_family=str(source_waveform_family),
        finite_tail_mode=finite_tail_mode,
        continuous_loop_output=continuous_loop_output,
        source_metadata=dict(source_metadata or {}),
    )


def run_finite_first_modeling(target_config: TargetConfig, source_selection: dict[str, Any]) -> ModelingResult:
    if not source_selection:
        return _missing_source("finite source is not selected", target_config, FINITE_FIRST_REQUIRED_API)
    source = read_source_dataframe(source_selection)
    if source.status != "ok" or source.command_profile is None:
        source.metadata.update(_input_metadata(target_config, source_selection, FINITE_FIRST_REQUIRED_API, ready=False))
        return source
    schema = validate_finite_first_input_frame(source.command_profile)
    if schema["status"] != "ok":
        return ModelingResult(
            status="schema_unavailable",
            metadata={
                **_input_metadata(target_config, source_selection, FINITE_FIRST_REQUIRED_API, ready=False),
                "missing_column_groups": schema["missing_column_groups"],
                "required_column_candidates": schema["required_column_candidates"],
                "resolved_columns": schema["resolved_columns"],
            },
            warnings=[],
            error_reason="finite first source schema is unavailable",
        )
    try:
        from coil_win_app.core_dependency import import_core_module

        imported = import_core_module("field_analysis.finite_first_phase_sync")
    except Exception as exc:
        imported = {"status": "failed", "core_import_error": str(exc), "module": None}
    if imported["status"] != "ok":
        return _not_connected(
            f"finite first modeling core dependency is not connected: {imported['core_import_error']}",
            target_config,
            source_selection,
            required_api=FINITE_FIRST_REQUIRED_API,
        )
    apply_fn = getattr(imported["module"], "apply_finite_first_phase_sync_modeling", None)
    if apply_fn is None:
        return _not_connected("finite first core API is unavailable", target_config, source_selection, required_api=FINITE_FIRST_REQUIRED_API)
    try:
        output = apply_fn(
            source.command_profile,
            freq_hz=target_config.freq_hz,
            cycle_count=target_config.cycle_count,
            target_peak_field_mT=target_config.target_peak_field_mT,
            voltage_limit_v=target_config.voltage_limit_v,
            mode="phase_synced",
        )
    except Exception as exc:
        return ModelingResult(
            status="failed",
            metadata=_input_metadata(target_config, source_selection, FINITE_FIRST_REQUIRED_API, ready=True),
            warnings=[],
            error_reason=f"finite first core call failed: {exc}",
        )
    result = _wrap_core_output(output)
    if result.status == "ok":
        result.metadata.update(_input_metadata(target_config, source_selection, FINITE_FIRST_REQUIRED_API, ready=True))
        result.metadata["core_bridge_used"] = True
        result.metadata["finite_first_bridge_version"] = "phase_synced_field_per_volt_aware"
        result.metadata.setdefault("final_voltage_limit_v", target_config.voltage_limit_v)
    return result


def run_finite_second_modeling(target_config: TargetConfig, first_result: ModelingResult, actual_drive_source: dict[str, Any]) -> ModelingResult:
    required_api = "field_analysis.finite_second_modeling.run_finite_second_modeling"
    if not actual_drive_source:
        return _missing_actual_drive_source("actual-drive source is not selected", target_config, required_api)
    return _not_connected("finite second modeling core dependency is not connected", target_config, actual_drive_source, required_api=required_api)


def run_continuous_extraction(target_config: TargetConfig, continuous_source: dict[str, Any]) -> ModelingResult:
    required_api = "field_analysis.continuous_steady_state_runtime.run_continuous_steady_state_extraction"
    if not continuous_source:
        return _missing_source("continuous source is not selected", target_config, required_api)
    return _not_connected("continuous extraction core dependency is not connected", target_config, continuous_source, required_api=required_api)


def run_continuous_first_modeling(target_config: TargetConfig, extraction_result: ModelingResult) -> ModelingResult:
    required_api = "field_analysis.continuous_first_modeling.run_continuous_first_modeling"
    return _not_connected("continuous first modeling core dependency is not connected", target_config, required_api=required_api)


def run_continuous_second_modeling(target_config: TargetConfig, first_result: ModelingResult, actual_drive_source: dict[str, Any]) -> ModelingResult:
    required_api = "field_analysis.continuous_second_modeling.run_continuous_second_modeling"
    if not actual_drive_source:
        return _missing_actual_drive_source("actual-drive source is not selected", target_config, required_api)
    return _not_connected("continuous second modeling core dependency is not connected", target_config, actual_drive_source, required_api=required_api)


def build_final_lut_export(modeling_result: ModelingResult) -> ModelingResult:
    if modeling_result.metadata.get("result_kind") == "source_preview":
        return _failed("source preview result is not a final LUT export candidate")
    profile = modeling_result.command_profile
    if profile is None:
        return _failed("command_profile is missing")
    missing = [column for column in ("time_s", "limited_voltage_v") if column not in profile.columns]
    if missing:
        return _failed(f"command_profile missing required columns: {', '.join(missing)}")
    export_frame = pd.DataFrame({"sample_index": range(len(profile)), "time_s": profile["time_s"].to_numpy(), "voltage_v": profile["limited_voltage_v"].to_numpy()})
    return ModelingResult(
        status="ok",
        metadata={"export_columns": ["sample_index", "time_s", "voltage_v"], "voltage_source_column": "limited_voltage_v", "fourier_resynthesis": False},
        warnings=[],
        command_profile=profile,
        export_frame=export_frame,
    )


def create_demo_modeling_result() -> ModelingResult:
    command_profile = pd.DataFrame({"time_s": [0.0, 0.001, 0.002, 0.003], "limited_voltage_v": [0.0, 2.5, -2.5, 0.0]})
    return ModelingResult(
        status="ok",
        metadata={"demo_only": True, "note": "Demo only / modeling result 아님", "voltage_limit_v": VOLTAGE_LIMIT_V},
        warnings=["Demo only / modeling result 아님"],
        command_profile=command_profile,
    )


def _wrap_core_output(output: Any) -> ModelingResult:
    if isinstance(output, ModelingResult):
        return output
    if isinstance(output, pd.DataFrame):
        return ModelingResult(status="ok", metadata={}, warnings=[], command_profile=output)
    if isinstance(output, dict):
        profile = output.get("command_profile")
        if profile is None and isinstance(output.get("command_profile_df"), pd.DataFrame):
            profile = output["command_profile_df"]
        if isinstance(profile, pd.DataFrame):
            return ModelingResult(status=str(output.get("status", "ok")), metadata=dict(output.get("metadata", {})), warnings=list(output.get("warnings", [])), command_profile=profile)
    return _failed(f"finite first core returned unsupported type: {type(output).__name__}")


def _not_connected(reason: str, *context: Any, required_api: str = "") -> ModelingResult:
    metadata = _input_metadata_from_context(context, required_api)
    return ModelingResult(status="not_connected", metadata=metadata, warnings=[], error_reason=reason)


def _failed(reason: str) -> ModelingResult:
    return ModelingResult(status="failed", metadata={}, warnings=[], error_reason=reason)


def _missing_source(reason: str, target_config: TargetConfig | None, required_api: str) -> ModelingResult:
    metadata = {"core_repo": CORE_REPO, "core_sha": CORE_SHA, "adapter_input_contract_ready": False, "required_core_api": required_api}
    if target_config is not None:
        metadata["target_config"] = asdict(target_config)
    return ModelingResult(status="missing_source", metadata=metadata, warnings=[], error_reason=reason)


def _missing_actual_drive_source(reason: str, target_config: TargetConfig, required_api: str) -> ModelingResult:
    return ModelingResult(status="missing_actual_drive_source", metadata=_input_metadata(target_config, {}, required_api, ready=False), warnings=[], error_reason=reason)


def _input_metadata_from_context(context: tuple[Any, ...], required_api: str) -> dict[str, Any]:
    target_config = next((value for value in context if isinstance(value, TargetConfig)), None)
    source = next((value for value in context if isinstance(value, dict)), {})
    ready = bool(target_config is not None and source.get("filename"))
    return _input_metadata(target_config, source, required_api, ready)


def _input_metadata(target_config: TargetConfig | None, source: dict[str, Any], required_api: str, ready: bool) -> dict[str, Any]:
    metadata: dict[str, Any] = {"core_repo": CORE_REPO, "core_sha": CORE_SHA, "adapter_input_contract_ready": ready, "required_core_api": required_api}
    if target_config is not None:
        metadata["target_config"] = asdict(target_config)
    if source.get("filename"):
        metadata["selected_source_filename"] = source.get("filename")
        metadata["selected_source_path"] = source.get("path")
        metadata["selected_source_category"] = source.get("category")
    return metadata


def _scan_source_records(root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    paths = sorted((path for path in root.rglob("*") if path.is_file()), key=lambda path: path.name.lower())
    for path in paths:
        category, reason = _infer_source_category(path.name)
        records.append({"path": str(path), "filename": path.name, "category": category, "reason": reason})
    return records


def _count_source_records(records: list[dict[str, str]]) -> dict[str, int]:
    counts = {"finite": 0, "continuous": 0, "actual_drive": 0, "unknown": 0}
    for record in records:
        counts[record["category"]] += 1
    return counts


def _infer_source_category(filename: str) -> tuple[str, str]:
    name = filename.lower()
    if "transient_1st_result" in name or "continuous_1st_result" in name:
        return "actual_drive", "keyword_match"
    if "result" in name or "actual" in name or "validation" in name:
        return "actual_drive", "keyword_match"
    if name.startswith("finite_"):
        return "finite", "filename_pattern"
    if name.startswith("continuous_"):
        return "continuous", "filename_pattern"
    if "finite" in name:
        return "finite", "keyword_match"
    if "continuous" in name:
        return "continuous", "keyword_match"
    return "unknown", "unknown"
