from __future__ import annotations


def test_format_core_status_distinguishes_split_dependency_states() -> None:
    from coil_win_app.ui.project_page import _format_core_status_from_dependency

    text = _format_core_status_from_dependency(
        {
            "core_sha": "abc123",
            "core_path_configured": False,
            "core_package_import_available": False,
            "finite_first_core_available": False,
            "finite_first_api_available": False,
            "configured_core_path": None,
            "missing_finite_first_modules": ["field_analysis.finite_first_phase_sync"],
            "missing_optional_workflow_modules": ["field_analysis.continuous_first_modeling"],
            "api_missing_reason": "No module named field_analysis",
            "streamlit_imported": False,
            "forbidden_module_status": {"streamlit": {"loaded": False}},
        }
    )

    assert "core path configured=no" in text
    assert "core package available=no" in text
    assert "finite first core available=no" in text
    assert "finite first API available=no" in text
    assert "expected SHA=abc123" in text
    assert "configured path=none" in text
    assert "missing finite first modules=field_analysis.finite_first_phase_sync" in text
    assert "missing optional workflow modules=field_analysis.continuous_first_modeling" in text
    assert "api missing reason=No module named field_analysis" in text
    assert "streamlit imported=no" in text
    assert "forbidden loaded=none" in text


def test_format_core_status_reports_forbidden_loaded() -> None:
    from coil_win_app.ui.project_page import _format_core_status_from_dependency

    text = _format_core_status_from_dependency(
        {
            "core_sha": "abc123",
            "core_path_configured": True,
            "core_package_import_available": True,
            "finite_first_core_available": True,
            "finite_first_api_available": True,
            "configured_core_path": "D:/core/src",
            "missing_finite_first_modules": [],
            "missing_optional_workflow_modules": [],
            "api_missing_reason": "",
            "streamlit_imported": True,
            "forbidden_module_status": {
                "streamlit": {"loaded": True},
                "field_analysis.app_ui_snapshot": {"loaded": True},
            },
        }
    )

    assert "forbidden loaded=field_analysis.app_ui_snapshot, streamlit" in text
