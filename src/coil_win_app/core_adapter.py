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
CORE_SHA = "8f8a881b040429a4d6451f15831602d2e76added"


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
    counts = _scan_source_counts(root)
    return ModelingResult(
        status="ok",
        metadata={"project_path": str(root), "source_counts": counts},
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


def _not_connected(reason: str, *_context: Any) -> ModelingResult:
    return ModelingResult(
        status="not_connected",
        metadata={"core_repo": CORE_REPO, "core_sha": CORE_SHA},
        warnings=[],
        error_reason=reason,
    )


def _failed(reason: str) -> ModelingResult:
    return ModelingResult(status="failed", metadata={}, warnings=[], error_reason=reason)


def _scan_source_counts(root: Path) -> dict[str, int]:
    counts = {"finite": 0, "continuous": 0, "actual_drive": 0, "unknown": 0}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.startswith("finite_"):
            counts["finite"] += 1
        elif name.startswith("continuous_"):
            counts["continuous"] += 1
        elif "result" in name or "actual" in name or "validation" in name:
            counts["actual_drive"] += 1
        else:
            counts["unknown"] += 1
    return counts
