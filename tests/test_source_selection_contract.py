from __future__ import annotations


def test_project_state_stores_selected_source_records() -> None:
    from coil_win_app.project_state import ProjectState

    finite = {"filename": "finite_sine_1Hz_1.0cycle.csv", "category": "finite"}
    continuous = {"filename": "continuous_sine_1Hz.csv", "category": "continuous"}
    actual_drive = {"filename": "run_result.csv", "category": "actual_drive"}

    state = ProjectState()
    state.selected_finite_source = finite
    state.selected_continuous_source = continuous
    state.selected_actual_drive_source = actual_drive

    assert state.selected_finite_source == finite
    assert state.selected_continuous_source == continuous
    assert state.selected_actual_drive_source == actual_drive


def test_modeling_pages_pass_selected_source_records() -> None:
    finite_source = open("src/coil_win_app/ui/finite_modeling_page.py", encoding="utf-8").read()
    continuous_source = open("src/coil_win_app/ui/continuous_modeling_page.py", encoding="utf-8").read()

    assert "state.selected_finite_source or {}" in finite_source
    assert "state.selected_continuous_source or {}" in continuous_source
    assert "Selected finite source" in finite_source
    assert "Selected continuous source" in continuous_source
    assert "Selected actual-drive source" in finite_source
    assert "filename" in finite_source


def test_project_page_lists_and_selects_sources() -> None:
    source = open("src/coil_win_app/ui/project_page.py", encoding="utf-8").read()

    assert "Finite source" in source
    assert "Continuous source" in source
    assert "Actual-drive source" in source
    assert "unknown source list" in source
    assert "selected_finite_source" in source
    assert "selected_continuous_source" in source
    assert "selected_actual_drive_source" in source
    assert "selected finite source:" in source
    assert "selected continuous source:" in source
    assert "selected actual-drive source:" in source


def test_project_page_has_readable_section_styles() -> None:
    source = open("src/coil_win_app/ui/project_page.py", encoding="utf-8").read()

    assert "_section_title" in source
    assert "_info_label" in source
    assert "_selected_label_widget" in source
    assert "font-size: 16px" in source
    assert "font-weight: 700" in source
    assert "background-color" in source
    assert "SOURCE SELECTION" in source
    assert "SOURCE INVENTORY" in source
