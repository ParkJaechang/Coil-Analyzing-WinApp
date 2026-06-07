from __future__ import annotations

import pandas as pd


def test_finite_first_summary_for_ok_result() -> None:
    from coil_win_app.core_adapter import ModelingResult
    from coil_win_app.result_diagnostics import explain_final_lut_export_eligibility, summarize_finite_first_result

    result = ModelingResult(
        status="ok",
        metadata={
            "selected_source_filename": "finite_sine_1Hz.csv",
            "required_core_api": "field_analysis.finite_first_phase_sync.apply_finite_first_phase_sync_modeling",
            "finite_first_modeling_status": "ok",
            "core_bridge_used": True,
            "finite_first_input_schema": {"resolved_columns": {"time": "time_s"}, "missing_column_groups": []},
            "final_voltage_limit_v": 10.0,
            "field_per_volt_mT_per_v": 8.0,
            "voltage_per_field_v_per_mT": 0.125,
            "clipping_fraction": 0.0,
            "phase_delay_s": 0.01,
            "phase_delay_cycles": 0.02,
            "positive_peak_error_ratio": 0.1,
        },
        warnings=[],
        command_profile=pd.DataFrame({"time_s": [0.0, 0.1], "limited_voltage_v": [0.0, -2.5]}),
    )

    summary = summarize_finite_first_result(result)
    eligibility = explain_final_lut_export_eligibility(result)

    assert summary["status"] == "ok"
    assert summary["selected_source_filename"] == "finite_sine_1Hz.csv"
    assert summary["command_profile_row_count"] == 2
    assert summary["has_time_s"] is True
    assert summary["has_limited_voltage_v"] is True
    assert summary["limited_voltage_v_peak"] == 2.5
    assert summary["field_per_volt_mT_per_v"] == 8.0
    assert summary["peak_error_ratios"]["positive_peak_error_ratio"] == 0.1
    assert summary["final_export_candidate"] is True
    assert eligibility["eligible"] is True


def test_finite_first_summary_for_schema_unavailable_result() -> None:
    from coil_win_app.core_adapter import ModelingResult
    from coil_win_app.result_diagnostics import summarize_finite_first_result

    result = ModelingResult(
        status="schema_unavailable",
        metadata={
            "missing_column_groups": ["voltage"],
            "resolved_columns": {"time": "time_s"},
            "required_core_api": "api",
        },
        warnings=[],
        error_reason="finite first source schema is unavailable",
    )

    summary = summarize_finite_first_result(result)

    assert summary["status"] == "schema_unavailable"
    assert summary["error_reason"] == "finite first source schema is unavailable"
    assert summary["finite_first_input_schema"]["missing_column_groups"] == ["voltage"]
    assert summary["final_export_candidate"] is False
    assert "schema_unavailable" in summary["final_export_blocking_reason"]


def test_finite_first_summary_for_not_connected_result() -> None:
    from coil_win_app.core_adapter import ModelingResult
    from coil_win_app.result_diagnostics import summarize_finite_first_result

    result = ModelingResult(
        status="not_connected",
        metadata={"required_core_api": "api", "missing_core_modules": ["field_analysis.finite_first_phase_sync"]},
        warnings=[],
        error_reason="core missing",
    )

    summary = summarize_finite_first_result(result)

    assert summary["status"] == "not_connected"
    assert summary["required_core_api"] == "api"
    assert summary["final_export_candidate"] is False
    assert "not_connected" in summary["final_export_blocking_reason"]


def test_export_eligibility_rejects_blocked_cases() -> None:
    from coil_win_app.core_adapter import ModelingResult, create_demo_modeling_result
    from coil_win_app.result_diagnostics import explain_final_lut_export_eligibility

    ok_profile = pd.DataFrame({"time_s": [0.0, 0.1], "limited_voltage_v": [0.0, 1.0]})

    cases = [
        ModelingResult(status="failed", metadata={}, warnings=[], command_profile=ok_profile),
        ModelingResult(status="ok", metadata={"result_kind": "source_preview"}, warnings=[], command_profile=ok_profile),
        ModelingResult(status="ok", metadata={"result_kind": "source_dataframe"}, warnings=[], command_profile=ok_profile),
        create_demo_modeling_result(),
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
            metadata={"finite_first_modeling_status": "peak_detection_failed"},
            warnings=[],
            command_profile=ok_profile,
        ),
    ]

    for result in cases:
        eligibility = explain_final_lut_export_eligibility(result)
        assert eligibility["eligible"] is False
        assert eligibility["blocking_reason"]


def test_export_eligibility_allows_explicit_demo_path() -> None:
    from coil_win_app.core_adapter import create_demo_modeling_result
    from coil_win_app.result_diagnostics import explain_final_lut_export_eligibility

    assert explain_final_lut_export_eligibility(create_demo_modeling_result(), allow_demo=True)["eligible"] is True
