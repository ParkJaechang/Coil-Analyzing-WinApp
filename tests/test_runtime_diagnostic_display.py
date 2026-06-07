from __future__ import annotations


def test_runtime_diagnostic_text_does_not_import_streamlit() -> None:
    import sys

    from coil_win_app.runtime_diagnostics import format_runtime_diagnostic_packet

    sys.modules.pop("streamlit", None)
    text = format_runtime_diagnostic_packet(
        {
            "expected_core_sha": "expected",
            "actual_core_sha": "actual",
            "actual_core_sha_matches_expected": False,
            "configured_core_path": "D:/core/src",
            "environment_core_src": None,
            "streamlit_imported": False,
            "forbidden_module_status": {"streamlit": {"loaded": False}},
            "finite_first_api": {"status": "ok", "signature": "(command_profile, **kwargs)"},
            "helper_api_status": {"helper": {"status": "ok"}},
            "module_status": {"field_analysis.finite_first_phase_sync": {"status": "ok"}},
        }
    )

    assert "expected_core_sha" in text
    assert "actual_core_sha" in text
    assert "finite_first_api" in text
    assert "helper_api_status_summary" in text
    assert "streamlit" not in sys.modules


def test_runtime_diagnostic_compact_packet_includes_missing_modules() -> None:
    from coil_win_app.runtime_diagnostics import compact_runtime_diagnostic_packet

    compact = compact_runtime_diagnostic_packet(
        {
            "expected_core_sha": "expected",
            "actual_core_sha": None,
            "actual_core_sha_matches_expected": None,
            "configured_core_path": None,
            "environment_core_src": "D:/core",
            "streamlit_imported": False,
            "forbidden_module_status": {},
            "finite_first_api": {"status": "failed", "signature": None},
            "helper_api_status": {"helper_a": {"status": "ok"}, "helper_b": {"status": "failed"}},
            "module_status": {
                "field_analysis.finite_first_phase_sync": {"status": "failed"},
                "field_analysis.finite_second_modeling": {"status": "failed"},
                "field_analysis.continuous_first_modeling": {"status": "failed"},
            },
        }
    )

    assert compact["expected_core_sha"] == "expected"
    assert compact["environment_core_src"] == "D:/core"
    assert compact["finite_first_api"]["status"] == "failed"
    assert compact["helper_api_status_summary"] == {"ok": 1, "failed": 1}
    assert "field_analysis.finite_first_phase_sync" in compact["missing_finite_first_modules"]
    assert "field_analysis.continuous_first_modeling" in compact["missing_optional_workflow_modules"]
