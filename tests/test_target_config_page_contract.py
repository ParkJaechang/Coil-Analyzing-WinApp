from __future__ import annotations


def test_target_config_page_accepts_project_state() -> None:
    source = open("src/coil_win_app/ui/target_config_page.py", encoding="utf-8").read()

    assert "def create_target_config_page(state: ProjectState)" in source
    assert "state.set_target_config(config)" in source
    assert "continuous mode locks cycle_count to 1.0" in source


def test_modeling_and_export_pages_use_project_state() -> None:
    finite_source = open("src/coil_win_app/ui/finite_modeling_page.py", encoding="utf-8").read()
    continuous_source = open("src/coil_win_app/ui/continuous_modeling_page.py", encoding="utf-8").read()
    export_source = open("src/coil_win_app/ui/final_export_page.py", encoding="utf-8").read()

    assert "Target Config를 먼저 설정하십시오." in finite_source
    assert "run_finite_first_modeling" in finite_source
    assert "state.latest_finite_first_result" in finite_source
    assert "run_continuous_extraction" in continuous_source
    assert "state.latest_continuous_first_result" in continuous_source
    assert "create_demo_modeling_result" in export_source
    assert "demo_only=True" in export_source
