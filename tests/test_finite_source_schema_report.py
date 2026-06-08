from __future__ import annotations

import pandas as pd


def test_finite_schema_report_accepts_actual_drive_columns() -> None:
    from coil_win_app.finite_source_schema import build_finite_first_source_schema_report

    frame = pd.DataFrame(
        {
            "TimeMs": [0.0, 1.0],
            "Voltage1_V": [0.0, 1.0],
            "HallBz": [0.0, -2.0],
            "target_output": [0.0, 2.0],
        }
    )

    report = build_finite_first_source_schema_report(frame)

    assert report["status"] == "ok"
    assert report["missing_column_groups"] == []
    assert report["resolved_columns"]["time"] == "TimeMs"
    assert report["resolved_columns"]["voltage"] == "Voltage1_V"
    assert report["row_count"] == 2
    assert report["numeric_finite_counts"]["voltage"] == 2
    assert report["final_lut_input_rejected"] is False


def test_finite_schema_report_rejects_missing_and_inf_only_groups() -> None:
    from coil_win_app.finite_source_schema import build_finite_first_source_schema_report

    missing_voltage = pd.DataFrame({"time_s": [0.0, 0.1], "HallBz": [0.0, 1.0], "target_field_mT": [0.0, 1.0]})
    report = build_finite_first_source_schema_report(missing_voltage)
    assert report["status"] == "schema_unavailable"
    assert "voltage" in report["missing_column_groups"]

    inf_measured = pd.DataFrame(
        {"time_s": [0.0, 0.1], "Voltage1_V": [0.0, 1.0], "HallBz": [float("inf"), float("inf")], "target_field_mT": [0.0, 1.0]}
    )
    report = build_finite_first_source_schema_report(inf_measured)
    assert report["status"] == "schema_unavailable"
    assert "measured_field" in report["missing_column_groups"]


def test_finite_schema_report_rejects_final_lut_only_csv() -> None:
    from coil_win_app.finite_source_schema import build_finite_first_source_schema_report

    frame = pd.DataFrame({"sample_index": [0, 1], "time_s": [0.0, 0.1], "voltage_v": [0.0, 1.0]})

    report = build_finite_first_source_schema_report(frame)

    assert report["status"] == "schema_unavailable"
    assert report["rejected_reason"] == "final_lut_export_schema_is_not_finite_first_input"
    assert report["final_lut_input_rejected"] is True
