from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_final_lut_export_columns_exact() -> None:
    from coil_win_app.core_adapter import ModelingResult, build_final_lut_export

    command_profile = pd.DataFrame(
        {
            "time_s": [0.0, 0.1, 0.2],
            "limited_voltage_v": [0.0, 1.5, -1.0],
            "extra_debug": [9, 9, 9],
        }
    )
    result = ModelingResult(
        status="ok",
        metadata={"source": "unit"},
        warnings=[],
        command_profile=command_profile,
    )

    export = build_final_lut_export(result)

    assert export.status == "ok"
    assert list(export.export_frame.columns) == ["sample_index", "time_s", "voltage_v"]
    assert export.export_frame["voltage_v"].tolist() == command_profile["limited_voltage_v"].tolist()


def test_final_lut_export_rejects_missing_limited_voltage() -> None:
    from coil_win_app.core_adapter import ModelingResult, build_final_lut_export

    result = ModelingResult(
        status="ok",
        metadata={},
        warnings=[],
        command_profile=pd.DataFrame({"time_s": [0.0], "voltage_v": [1.0]}),
    )

    export = build_final_lut_export(result)

    assert export.status == "failed"
    assert export.export_frame is None
    assert "limited_voltage_v" in str(export.error_reason)


def test_demo_modeling_result_exports_with_exact_columns() -> None:
    from coil_win_app.core_adapter import build_final_lut_export, create_demo_modeling_result

    result = create_demo_modeling_result()
    blocked = build_final_lut_export(result)
    export = build_final_lut_export(result, allow_demo=True)

    assert result.metadata["demo_only"] is True
    assert blocked.status == "failed"
    assert "demo" in str(blocked.error_reason)
    assert export.status == "ok"
    assert list(export.export_frame.columns) == ["sample_index", "time_s", "voltage_v"]


def test_final_lut_export_rejects_non_ok_and_source_dataframe_results() -> None:
    from coil_win_app.core_adapter import ModelingResult, build_final_lut_export

    profile = pd.DataFrame({"time_s": [0.0], "limited_voltage_v": [1.0]})

    assert build_final_lut_export(ModelingResult(status="failed", metadata={}, warnings=[], command_profile=profile)).status == "failed"
    assert (
        build_final_lut_export(
            ModelingResult(status="ok", metadata={"result_kind": "source_dataframe"}, warnings=[], command_profile=profile)
        ).status
        == "failed"
    )


def test_final_lut_export_rejects_bad_values_and_non_monotonic_time() -> None:
    from coil_win_app.core_adapter import ModelingResult, build_final_lut_export

    non_finite = ModelingResult(
        status="ok",
        metadata={},
        warnings=[],
        command_profile=pd.DataFrame({"time_s": [0.0, float("nan")], "limited_voltage_v": [0.0, 1.0]}),
    )
    non_monotonic = ModelingResult(
        status="ok",
        metadata={},
        warnings=[],
        command_profile=pd.DataFrame({"time_s": [0.1, 0.0], "limited_voltage_v": [0.0, 1.0]}),
    )

    assert build_final_lut_export(non_finite).status == "failed"
    assert build_final_lut_export(non_monotonic).status == "failed"


def test_final_lut_export_rejects_infinite_time_and_voltage() -> None:
    from coil_win_app.core_adapter import ModelingResult, build_final_lut_export

    infinite_time = ModelingResult(
        status="ok",
        metadata={},
        warnings=[],
        command_profile=pd.DataFrame({"time_s": [0.0, float("inf")], "limited_voltage_v": [0.0, 1.0]}),
    )
    infinite_voltage = ModelingResult(
        status="ok",
        metadata={},
        warnings=[],
        command_profile=pd.DataFrame({"time_s": [0.0, 0.1], "limited_voltage_v": [0.0, float("-inf")]}),
    )

    assert build_final_lut_export(infinite_time).status == "failed"
    assert build_final_lut_export(infinite_voltage).status == "failed"


def test_final_lut_export_rejects_non_ok_finite_first_metadata() -> None:
    from coil_win_app.core_adapter import ModelingResult, build_final_lut_export

    result = ModelingResult(
        status="ok",
        metadata={"finite_first_modeling_status": "peak_detection_failed"},
        warnings=[],
        command_profile=pd.DataFrame({"time_s": [0.0], "limited_voltage_v": [1.0]}),
    )

    export = build_final_lut_export(result)

    assert export.status == "failed"
    assert "peak_detection_failed" in str(export.error_reason)


def test_no_generated_user_data_committed() -> None:
    forbidden_suffixes = {".csv", ".xlsx", ".xlsm", ".xls"}
    repo_root = Path.cwd()
    offenders = []

    for path in repo_root.rglob("*"):
        if ".git" in path.parts or path.is_dir():
            continue
        if "Data" in path.parts:
            continue
        if "tests" in path.parts and "fixtures" in path.parts:
            continue
        if path.suffix.lower() in forbidden_suffixes:
            offenders.append(path.as_posix())

    assert offenders == []
