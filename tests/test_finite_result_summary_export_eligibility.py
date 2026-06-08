from __future__ import annotations

import pandas as pd


def _ok_result():
    from coil_win_app.core_adapter import ModelingResult

    return ModelingResult(
        status="ok",
        metadata={
            "selected_source_filename": "finite_sine_1Hz.csv",
            "selected_source_category": "finite",
            "selected_source_path": "D:/data/finite_sine_1Hz.csv",
            "required_core_api": "field_analysis.finite_first_phase_sync.apply_finite_first_phase_sync_modeling",
            "target_config": {"freq_hz": 1.0, "cycle_count": 1.5, "target_peak_field_mT": 50.0, "voltage_limit_v": 10.0},
            "finite_first_modeling_status": "ok",
            "core_bridge_used": True,
            "finite_first_bridge_version": "phase_synced_field_per_volt_aware",
            "finite_first_input_schema": {
                "status": "ok",
                "resolved_columns": {"time": "time_s", "voltage": "Voltage1_V"},
                "missing_column_groups": [],
                "prepared_columns": ["time_s", "limited_voltage_v"],
            },
            "final_voltage_limit_v": 10.0,
            "field_per_volt_mT_per_v": 8.0,
            "voltage_per_field_v_per_mT": 0.125,
            "residual_to_voltage_conversion_basis": "field_per_volt",
            "correction_delta_mode": "residual_proportional",
            "clipping_fraction": 0.0,
            "phase_sync_method": "midpoint",
            "phase_delay_s": 0.01,
            "phase_delay_cycles": 0.02,
            "positive_peak_error_ratio": 0.1,
            "negative_peak_error_ratio": -0.1,
            "peak_to_peak_error_ratio": 0.2,
        },
        warnings=[],
        command_profile=pd.DataFrame({"time_s": [0.0, 0.1], "limited_voltage_v": [0.0, -2.5]}),
    )


def test_finite_first_summary_for_ok_result() -> None:
    from coil_win_app.result_diagnostics import summarize_finite_first_result

    summary = summarize_finite_first_result(_ok_result())

    assert summary["status"] == "ok"
    assert summary["selected_source_filename"] == "finite_sine_1Hz.csv"
    assert summary["target_config"]["freq_hz"] == 1.0
    assert summary["command_profile_row_count"] == 2
    assert summary["command_profile_columns"] == ["time_s", "limited_voltage_v"]
    assert summary["has_time_s"] is True
    assert summary["has_limited_voltage_v"] is True
    assert summary["limited_voltage_v_peak"] == 2.5
    assert summary["final_export_candidate"] is True
    assert summary["peak_to_peak_error_ratio"] == 0.2


def test_finite_first_summary_for_non_ok_results() -> None:
    from coil_win_app.core_adapter import ModelingResult
    from coil_win_app.result_diagnostics import summarize_finite_first_result

    for status in ("schema_unavailable", "not_connected", "failed"):
        result = ModelingResult(status=status, metadata={"required_core_api": "api"}, warnings=[], error_reason=f"{status} reason")
        summary = summarize_finite_first_result(result)
        assert summary["status"] == status
        assert summary["error_reason"] == f"{status} reason"
        assert summary["final_export_candidate"] is False
        assert summary["final_export_blocking_reason"]

    result = _ok_result()
    result.metadata["finite_first_modeling_status"] = "peak_detection_failed"
    summary = summarize_finite_first_result(result)
    assert summary["final_export_candidate"] is False
    assert "peak_detection_failed" in summary["final_export_blocking_reason"]


def test_export_eligibility_accepts_and_rejects_required_cases() -> None:
    from coil_win_app.core_adapter import ModelingResult, create_demo_modeling_result
    from coil_win_app.result_diagnostics import explain_final_lut_export_eligibility

    assert explain_final_lut_export_eligibility(_ok_result())["eligible"] is True

    ok_profile = pd.DataFrame({"time_s": [0.0, 0.1], "limited_voltage_v": [0.0, 1.0]})
    cases = [
        ModelingResult(status="failed", metadata={}, warnings=[], command_profile=ok_profile),
        ModelingResult(status="ok", metadata={"result_kind": "source_preview"}, warnings=[], command_profile=ok_profile),
        ModelingResult(status="ok", metadata={"result_kind": "source_dataframe"}, warnings=[], command_profile=ok_profile),
        create_demo_modeling_result(),
        ModelingResult(status="ok", metadata={}, warnings=[], command_profile=None),
        ModelingResult(status="ok", metadata={}, warnings=[], command_profile=pd.DataFrame({"time_s": [], "limited_voltage_v": []})),
        ModelingResult(status="ok", metadata={}, warnings=[], command_profile=pd.DataFrame({"limited_voltage_v": [1.0]})),
        ModelingResult(status="ok", metadata={}, warnings=[], command_profile=pd.DataFrame({"time_s": [0.0]})),
        ModelingResult(
            status="ok",
            metadata={},
            warnings=[],
            command_profile=pd.DataFrame({"time_s": [0.0, float("inf")], "limited_voltage_v": [0.0, 1.0]}),
        ),
        ModelingResult(
            status="ok",
            metadata={},
            warnings=[],
            command_profile=pd.DataFrame({"time_s": [0.1, 0.0], "limited_voltage_v": [0.0, 1.0]}),
        ),
        ModelingResult(
            status="ok",
            metadata={"finite_first_modeling_status": "failed"},
            warnings=[],
            command_profile=ok_profile,
        ),
    ]
    for result in cases:
        eligibility = explain_final_lut_export_eligibility(result)
        assert eligibility["eligible"] is False
        assert eligibility["blocking_reason"]
