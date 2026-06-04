from __future__ import annotations

import pandas as pd


def test_finite_result_formatter_reports_schema_candidates() -> None:
    from coil_win_app.core_adapter import ModelingResult
    from coil_win_app.ui.finite_modeling_page import _format_result

    result = ModelingResult(
        status="schema_unavailable",
        metadata={
            "missing_column_groups": ["voltage", "target_field"],
            "required_column_candidates": {
                "voltage": ["limited_voltage_v", "Voltage1_V"],
                "target_field": ["physical_target_output_mT", "target_field_mT"],
            },
        },
        warnings=[],
        error_reason="finite first source schema is unavailable",
    )

    text = _format_result("finite first modeling", result)

    assert "missing column groups=voltage, target_field" in text
    assert "accepted column candidates:" in text
    assert "voltage: limited_voltage_v, Voltage1_V" in text


def test_finite_result_formatter_reports_core_status_for_not_connected() -> None:
    from coil_win_app.core_adapter import ModelingResult
    from coil_win_app.ui.finite_modeling_page import _format_result

    result = ModelingResult(
        status="not_connected",
        metadata={
            "required_core_api": "field_analysis.finite_first_phase_sync.apply_finite_first_phase_sync_modeling",
            "core_import_available": False,
            "missing_core_modules": ["field_analysis.finite_first_phase_sync"],
            "added_sys_path": "D:/core/src",
        },
        warnings=[],
        error_reason="finite first modeling core dependency is not connected",
    )

    text = _format_result("finite first modeling", result)

    assert "core import available=False" in text
    assert "missing core modules=field_analysis.finite_first_phase_sync" in text
    assert "added sys.path=D:/core/src" in text


def test_finite_result_formatter_reports_ok_voltage_peak_and_metadata() -> None:
    from coil_win_app.core_adapter import ModelingResult
    from coil_win_app.ui.finite_modeling_page import _format_result

    result = ModelingResult(
        status="ok",
        metadata={"field_per_volt_mT_per_v": 8.5, "phase_sync_method": "midpoint"},
        warnings=[],
        command_profile=pd.DataFrame({"time_s": [0.0, 0.1], "limited_voltage_v": [0.0, -2.5]}),
    )

    text = _format_result("finite first modeling", result)

    assert "command_profile rows=2" in text
    assert "limited_voltage_v peak=2.5" in text
    assert "field_per_volt_mT_per_v=8.5" in text
