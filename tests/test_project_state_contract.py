from __future__ import annotations

import pandas as pd


def test_project_state_stores_target_config_and_results() -> None:
    from coil_win_app.core_adapter import ModelingResult, build_target_config
    from coil_win_app.project_state import ProjectState

    state = ProjectState()
    config = build_target_config(
        modeling_input_mode="finite_startup_aware",
        freq_hz=1.0,
        cycle_count=1.0,
        target_peak_field_mT=60.0,
    )
    result = ModelingResult(
        status="ok",
        metadata={"demo_only": True},
        warnings=[],
        command_profile=pd.DataFrame({"time_s": [0.0], "limited_voltage_v": [0.0]}),
    )

    state.set_target_config(config)
    state.latest_finite_first_result = result
    state.add_status("target config saved")

    assert state.target_config == config
    assert state.latest_finite_first_result is result
    assert state.status_messages[-1] == "target config saved"


def test_project_state_source_selection_fields_are_explicit() -> None:
    from coil_win_app.project_state import ProjectState

    state = ProjectState()

    assert state.selected_finite_source is None
    assert state.selected_continuous_source is None
    state.selected_finite_source = {"source_id": "finite_001"}
    state.selected_continuous_source = {"source_id": "continuous_001"}

    assert state.selected_finite_source["source_id"] == "finite_001"
    assert state.selected_continuous_source["source_id"] == "continuous_001"
