from __future__ import annotations

import pandas as pd


def test_finite_first_schema_validation_ok_with_supported_columns() -> None:
    from coil_win_app.core_adapter import validate_finite_first_input_frame

    frame = pd.DataFrame(
        {
            "TimeMs": [0.0, 1.0],
            "Voltage1_V": [0.0, 1.0],
            "HallBz": [0.0, -10.0],
            "physical_target_output_mT": [0.0, 10.0],
        }
    )

    result = validate_finite_first_input_frame(frame)

    assert result["status"] == "ok"
    assert result["resolved_columns"]["time"] == "TimeMs"
    assert result["resolved_columns"]["voltage"] == "Voltage1_V"
    assert result["resolved_columns"]["measured_field"] == "HallBz"
    assert result["resolved_columns"]["target_field"] == "physical_target_output_mT"


def test_prepare_finite_first_input_frame_maps_aliases_without_dropping_raw_columns() -> None:
    from coil_win_app.core_adapter import prepare_finite_first_input_frame

    frame = pd.DataFrame(
        {
            "TimeMs": [0.0, 10.0],
            "Voltage1_V": [0.0, 1.0],
            "HallBz": [0.0, -10.0],
            "target_output": [0.0, 10.0],
        }
    )

    prepared, metadata = prepare_finite_first_input_frame(frame)

    assert metadata["status"] == "ok"
    assert metadata["resolved_columns"]["time"] == "TimeMs"
    assert metadata["resolved_columns"]["voltage"] == "Voltage1_V"
    assert metadata["resolved_columns"]["target_field"] == "target_output"
    assert prepared["time_s"].tolist() == [0.0, 0.01]
    assert prepared["limited_voltage_v"].tolist() == [0.0, 1.0]
    assert prepared["physical_target_output_mT"].tolist() == [0.0, 10.0]
    assert "HallBz" in prepared.columns
    assert "Voltage1_V" in prepared.columns


def test_prepare_finite_first_input_frame_rejects_final_lut_only_schema() -> None:
    from coil_win_app.core_adapter import prepare_finite_first_input_frame

    prepared, metadata = prepare_finite_first_input_frame(
        pd.DataFrame({"sample_index": [0, 1], "time_s": [0.0, 0.1], "voltage_v": [0.0, 1.0]})
    )

    assert prepared is None
    assert metadata["status"] == "schema_unavailable"
    assert metadata["rejected_reason"] == "final_lut_export_schema_is_not_finite_first_input"


def test_prepare_finite_first_input_frame_requires_numeric_finite_values() -> None:
    from coil_win_app.core_adapter import prepare_finite_first_input_frame

    _prepared, metadata = prepare_finite_first_input_frame(
        pd.DataFrame(
            {
                "time_s": [0.0, 0.1],
                "limited_voltage_v": ["bad", "nan"],
                "HallBz": [0.0, -1.0],
                "target_field_mT": [0.0, 1.0],
            }
        )
    )

    assert metadata["status"] == "schema_unavailable"
    assert "voltage" in metadata["missing_column_groups"]


def test_finite_first_schema_rejects_inf_only_voltage_column() -> None:
    from coil_win_app.core_adapter import validate_finite_first_input_frame

    result = validate_finite_first_input_frame(
        pd.DataFrame(
            {
                "time_s": [0.0, 0.1],
                "limited_voltage_v": [float("inf"), float("-inf")],
                "HallBz": [0.0, -1.0],
                "target_field_mT": [0.0, 1.0],
            }
        )
    )

    assert result["status"] == "schema_unavailable"
    assert "voltage" in result["missing_column_groups"]


def test_finite_first_schema_rejects_inf_only_time_measured_and_target_columns() -> None:
    from coil_win_app.core_adapter import validate_finite_first_input_frame

    result = validate_finite_first_input_frame(
        pd.DataFrame(
            {
                "time_s": [float("inf"), float("-inf")],
                "limited_voltage_v": [0.0, 1.0],
                "HallBz": [float("inf"), float("-inf")],
                "target_field_mT": [float("inf"), float("-inf")],
            }
        )
    )

    assert result["status"] == "schema_unavailable"
    assert "time" in result["missing_column_groups"]
    assert "measured_field" in result["missing_column_groups"]
    assert "target_field" in result["missing_column_groups"]


def test_finite_first_schema_validation_accepts_latest_column_aliases() -> None:
    from coil_win_app.core_adapter import validate_finite_first_input_frame

    frame = pd.DataFrame(
        {
            "time_s": [0.0, 0.1],
            "finite_first_input_lut_voltage_v": [0.0, 1.0],
            "raw_hallbz_mT": [0.0, -10.0],
            "aligned_target_output": [0.0, 10.0],
        }
    )

    result = validate_finite_first_input_frame(frame)

    assert result["status"] == "ok"
    assert result["resolved_columns"]["voltage"] == "finite_first_input_lut_voltage_v"
    assert result["resolved_columns"]["measured_field"] == "raw_hallbz_mT"
    assert result["resolved_columns"]["target_field"] == "aligned_target_output"


def test_finite_first_schema_validation_reports_missing_groups() -> None:
    from coil_win_app.core_adapter import validate_finite_first_input_frame

    result = validate_finite_first_input_frame(pd.DataFrame({"time_s": [0.0]}))

    assert result["status"] == "schema_unavailable"
    assert result["missing_column_groups"] == ["voltage", "measured_field", "target_field"]
    assert "voltage" in result["required_column_candidates"]
