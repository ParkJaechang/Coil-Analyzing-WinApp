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
