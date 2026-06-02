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
    export = build_final_lut_export(result)

    assert result.metadata["demo_only"] is True
    assert export.status == "ok"
    assert list(export.export_frame.columns) == ["sample_index", "time_s", "voltage_v"]


def test_no_generated_user_data_committed() -> None:
    forbidden_suffixes = {".csv", ".xlsx", ".xlsm", ".xls"}
    repo_root = Path.cwd()
    offenders = []

    for path in repo_root.rglob("*"):
        if ".git" in path.parts or path.is_dir():
            continue
        if "Data" in path.parts:
            continue
        if path.parts[:2] == ("tests", "fixtures"):
            continue
        if path.suffix.lower() in forbidden_suffixes:
            offenders.append(path.as_posix())

    assert offenders == []
