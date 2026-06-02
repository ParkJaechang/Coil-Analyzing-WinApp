from __future__ import annotations


def test_target_config_page_accepts_project_state() -> None:
    source = open("src/coil_win_app/ui/target_config_page.py", encoding="utf-8").read()

    assert "def create_target_config_page(state: ProjectState)" in source
    assert "state.set_target_config(config)" in source
    assert "TargetConfig saved" in source
    assert "continuous mode locks cycle_count to 1.0" in source
    assert "±10V (read-only policy)" in source


def test_modeling_and_export_pages_use_project_state() -> None:
    finite_source = open("src/coil_win_app/ui/finite_modeling_page.py", encoding="utf-8").read()
    continuous_source = open("src/coil_win_app/ui/continuous_modeling_page.py", encoding="utf-8").read()
    export_source = open("src/coil_win_app/ui/final_export_page.py", encoding="utf-8").read()

    assert "Target Config를 먼저 설정하십시오." in finite_source
    assert "Target Config를 먼저 설정하십시오." in continuous_source
    assert "run_finite_first_modeling" in finite_source
    assert "state.latest_finite_first_result" in finite_source
    assert "run_continuous_extraction" in continuous_source
    assert "state.latest_continuous_first_result" in continuous_source
    assert "create_demo_modeling_result" in export_source
    assert "demo_only=True" in export_source


def test_main_window_passes_shared_project_state_to_pages() -> None:
    source = open("src/coil_win_app/ui/main_window.py", encoding="utf-8").read()

    assert "create_project_page(self.state)" in source
    assert "create_target_config_page(self.state)" in source
    assert "create_finite_modeling_page(self.state)" in source
    assert "create_continuous_modeling_page(self.state)" in source
    assert "create_final_export_page(self.state)" in source


def test_winapp_ui_source_has_no_mojibake() -> None:
    source_paths = [
        "src/coil_win_app/core_adapter.py",
        "src/coil_win_app/project_state.py",
        "src/coil_win_app/ui/main_window.py",
        "src/coil_win_app/ui/project_page.py",
        "src/coil_win_app/ui/target_config_page.py",
        "src/coil_win_app/ui/finite_modeling_page.py",
        "src/coil_win_app/ui/continuous_modeling_page.py",
        "src/coil_win_app/ui/final_export_page.py",
    ]
    mojibake_markers = [
        chr(0xFFFD),
        chr(0xF9E4),
        chr(0xC496),
        "?" + chr(0xAFB8),
        chr(0xB97C) + "?",
        chr(0xBA3C) + chr(0xC1E0) + "?",
        "?" + chr(0x3145) + chr(0xC824) + chr(0xD560),
        chr(0xC12C) + chr(0xB5D7),
        chr(0xC9F9) + "10V",
    ]

    offenders: list[str] = []
    for path in source_paths:
        text = open(path, encoding="utf-8").read()
        for marker in mojibake_markers:
            if marker in text:
                offenders.append(f"{path}: {marker}")

    assert offenders == []
