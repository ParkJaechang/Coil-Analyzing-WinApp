from __future__ import annotations

import sys


def test_runtime_diagnostic_formatter_does_not_import_streamlit() -> None:
    from coil_win_app.runtime_diagnostics import format_runtime_diagnostic_packet

    sys.modules.pop("streamlit", None)
    text = format_runtime_diagnostic_packet(
        {
            "expected_core_repo": "ParkJaechang/Coil-Analyzing",
            "expected_core_sha": "expected",
            "configured_core_path": "D:/core/src",
            "configured_core_paths": ["D:/core/src"],
            "environment_core_src": None,
            "added_sys_path": "D:/core/src",
            "actual_core_sha": "actual",
            "actual_core_sha_matches_expected": False,
            "streamlit_imported": False,
            "forbidden_module_status": {"streamlit": {"loaded": False}},
            "module_status": {"field_analysis.finite_first_phase_sync": {"status": "ok"}},
            "finite_first_api": {"status": "ok", "signature": "(command_profile, **kwargs)", "module_file": "x.py"},
            "helper_api_status": {"helper_a": {"status": "ok"}, "helper_b": {"status": "failed"}},
        }
    )

    assert "expected_core_sha" in text
    assert "actual_core_sha" in text
    assert "actual_core_sha_matches_expected" in text
    assert "finite_first_api" in text
    assert "helper_api_status_summary" in text
    assert "streamlit" not in sys.modules


def test_core_status_summary_error_warning_ok_cases() -> None:
    from coil_win_app.runtime_diagnostics import build_core_status_summary

    no_path = build_core_status_summary(
        {
            "core_path_configured": False,
            "core_package_import_available": False,
            "finite_first_api_available": False,
            "missing_finite_first_modules": ["field_analysis.finite_first_phase_sync"],
            "missing_optional_workflow_modules": [],
            "actual_core_sha_matches_expected": None,
            "forbidden_module_status": {},
        }
    )
    assert no_path["severity"] == "error"
    assert no_path["blocking_reason"]

    optional_missing = build_core_status_summary(
        {
            "core_path_configured": True,
            "core_package_import_available": True,
            "finite_first_api_available": True,
            "missing_finite_first_modules": [],
            "missing_optional_workflow_modules": ["field_analysis.continuous_first_modeling"],
            "actual_core_sha_matches_expected": True,
            "forbidden_module_status": {},
        }
    )
    assert optional_missing["severity"] == "warning"

    ok = build_core_status_summary(
        {
            "core_path_configured": True,
            "core_package_import_available": True,
            "finite_first_api_available": True,
            "missing_finite_first_modules": [],
            "missing_optional_workflow_modules": [],
            "actual_core_sha_matches_expected": True,
            "forbidden_module_status": {},
        }
    )
    assert ok["severity"] == "ok"


def test_core_status_summary_derives_missing_finite_modules_from_raw_packet() -> None:
    from coil_win_app.runtime_diagnostics import build_core_status_summary

    raw_packet = {
        "configured_core_path": "D:/core/src",
        "actual_core_sha_matches_expected": True,
        "forbidden_module_status": {},
        "finite_first_api": {"status": "ok"},
        "module_status": {
            "field_analysis.finite_first_phase_sync": {"status": "ok"},
            "field_analysis.first_modeling_voltage_response": {"status": "ok"},
            "field_analysis.modeling_error_metrics": {"status": "ok"},
            "field_analysis.voltage_policy": {"status": "ok"},
            "field_analysis.final_modeled_lut": {"status": "failed"},
        },
    }

    summary = build_core_status_summary(raw_packet)

    assert summary["severity"] == "error"
    assert "missing finite-first modules" in summary["blocking_reason"]
    assert "field_analysis.final_modeled_lut" in summary["missing_finite_first_modules"]


def test_core_status_summary_derives_optional_only_missing_from_raw_packet() -> None:
    from coil_win_app.runtime_diagnostics import build_core_status_summary

    raw_packet = {
        "configured_core_path": "D:/core/src",
        "actual_core_sha_matches_expected": True,
        "forbidden_module_status": {},
        "finite_first_api": {"status": "ok"},
        "module_status": {
            "field_analysis.finite_first_phase_sync": {"status": "ok"},
            "field_analysis.first_modeling_voltage_response": {"status": "ok"},
            "field_analysis.modeling_error_metrics": {"status": "ok"},
            "field_analysis.voltage_policy": {"status": "ok"},
            "field_analysis.final_modeled_lut": {"status": "ok"},
            "field_analysis.continuous_first_modeling": {"status": "failed"},
        },
    }

    summary = build_core_status_summary(raw_packet)

    assert summary["severity"] == "warning"
    assert summary["blocking_reason"] is None
    assert summary["missing_finite_first_modules"] == []
    assert "field_analysis.continuous_first_modeling" in summary["missing_optional_workflow_modules"]


def test_project_page_wires_runtime_diagnostics_without_auto_file_writes() -> None:
    source = open("src/coil_win_app/ui/project_page.py", encoding="utf-8").read()

    assert "RUNTIME DIAGNOSTICS" in source
    assert "Show Runtime Diagnostic Packet" in source
    assert "build_runtime_diagnostic_packet" in source
    assert "format_runtime_diagnostic_packet" in source
    assert "open(" not in source
