from __future__ import annotations

from dataclasses import dataclass, field
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
    return {
        "core_repo": CORE_REPO,
        "core_sha": CORE_SHA,
        "adapter_status": "placeholder_not_connected",
    }


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
    return _not_connected("finite first modeling core dependency is not connected", target_config, source_selection)


def run_finite_second_modeling(
    target_config: TargetConfig,
    first_result: ModelingResult,
    actual_drive_source: dict[str, Any],
) -> ModelingResult:
    return _not_connected("finite second modeling core dependency is not connected", target_config, actual_drive_source)


def run_continuous_extraction(target_config: TargetConfig, continuous_source: dict[str, Any]) -> ModelingResult:
    return _not_connected("continuous extraction core dependency is not connected", target_config, continuous_source)


def run_continuous_first_modeling(target_config: TargetConfig, extraction_result: ModelingResult) -> ModelingResult:
    return _not_connected("continuous first modeling core dependency is not connected", target_config)


def run_continuous_second_modeling(
    target_config: TargetConfig,
    first_result: ModelingResult,
    actual_drive_source: dict[str, Any],
) -> ModelingResult:
    return _not_connected("continuous second modeling core dependency is not connected", target_config, actual_drive_source)


def build_final_lut_export(modeling_result: ModelingResult) -> ModelingResult:
    profile = modeling_result.command_profile
    if profile is None:
        return _failed("command_profile is missing")
    missing = [column for column in ("time_s", "limited_voltage_v") if column not in profile.columns]
    if missing:
        return _failed(f"command_profile missing required columns: {', '.join(missing)}")
    export_frame = pd.DataFrame(
        {
            "sample_index": range(len(profile)),
            "time_s": profile["time_s"].to_numpy(),
            "voltage_v": profile["limited_voltage_v"].to_numpy(),
        }
    )
    return ModelingResult(
        status="ok",
        metadata={
            "export_columns": ["sample_index", "time_s", "voltage_v"],
            "voltage_source_column": "limited_voltage_v",
            "fourier_resynthesis": False,
        },
        warnings=[],
        command_profile=profile,
        export_frame=export_frame,
    )


def create_demo_modeling_result() -> ModelingResult:
    command_profile = pd.DataFrame(
        {
            "time_s": [0.0, 0.001, 0.002, 0.003],
            "limited_voltage_v": [0.0, 2.5, -2.5, 0.0],
        }
    )
    return ModelingResult(
        status="ok",
        metadata={
            "demo_only": True,
            "note": "Demo only / modeling result 아님",
            "voltage_limit_v": VOLTAGE_LIMIT_V,
        },
        warnings=["Demo only / modeling result 아님"],
        command_profile=command_profile,
    )


def _not_connected(reason: str, *_context: Any) -> ModelingResult:
    metadata = {"core_repo": CORE_REPO, "core_sha": CORE_SHA}
    metadata.update(_context_metadata(_context))
    return ModelingResult(
        status="not_connected",
        metadata=metadata,
        warnings=[],
        error_reason=reason,
    )


def _failed(reason: str) -> ModelingResult:
    return ModelingResult(status="failed", metadata={}, warnings=[], error_reason=reason)


def _context_metadata(context: tuple[Any, ...]) -> dict[str, Any]:
    for value in context:
        if isinstance(value, dict) and value.get("filename"):
            return {
                "selected_source_filename": value["filename"],
                "selected_source_category": value.get("category"),
            }
    return {}


def _scan_source_records(root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    paths = sorted((path for path in root.rglob("*") if path.is_file()), key=lambda path: path.name.lower())
    for path in paths:
        records.append(
            {
                "path": str(path),
                "filename": path.name,
                "category": _infer_source_category(path.name),
                "reason": "filename_pattern",
            }
        )
    return records


def _count_source_records(records: list[dict[str, str]]) -> dict[str, int]:
    counts = {"finite": 0, "continuous": 0, "actual_drive": 0, "unknown": 0}
    for record in records:
        counts[record["category"]] += 1
    return counts


def _infer_source_category(filename: str) -> str:
    name = filename.lower()
    if "result" in name or "actual" in name or "validation" in name:
        return "actual_drive"
    if name.startswith("finite_"):
        return "finite"
    if name.startswith("continuous_"):
        return "continuous"
    return "unknown"
