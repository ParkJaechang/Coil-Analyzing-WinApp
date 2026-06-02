from __future__ import annotations


def _target_config():
    from coil_win_app.core_adapter import build_target_config

    return build_target_config(
        modeling_input_mode="finite_startup_aware",
        freq_hz=1.0,
        cycle_count=1.0,
        target_peak_field_mT=50.0,
    )


def test_finite_first_missing_source_is_not_core_not_connected() -> None:
    from coil_win_app.core_adapter import run_finite_first_modeling

    result = run_finite_first_modeling(_target_config(), {})

    assert result.status == "missing_source"
    assert result.metadata["adapter_input_contract_ready"] is False


def test_finite_first_not_connected_metadata_includes_target_and_source() -> None:
    from coil_win_app.core_adapter import run_finite_first_modeling

    source = {"filename": "finite_sine_1Hz.csv", "path": "C:/data/finite_sine_1Hz.csv", "category": "finite"}
    result = run_finite_first_modeling(_target_config(), source)

    assert result.status == "not_connected"
    assert result.metadata["adapter_input_contract_ready"] is True
    assert result.metadata["target_config"]["target_shape"] == "fixed_rounded_triangle"
    assert result.metadata["selected_source_filename"] == "finite_sine_1Hz.csv"
    assert result.metadata["selected_source_path"] == "C:/data/finite_sine_1Hz.csv"
    assert result.metadata["selected_source_category"] == "finite"
    assert result.metadata["required_core_api"]


def test_continuous_extraction_missing_source_is_explicit() -> None:
    from coil_win_app.core_adapter import build_target_config, run_continuous_extraction

    config = build_target_config(
        modeling_input_mode="continuous_steady_state",
        freq_hz=1.0,
        cycle_count=1.5,
        target_peak_field_mT=50.0,
    )
    result = run_continuous_extraction(config, {})

    assert result.status == "missing_source"
    assert result.metadata["adapter_input_contract_ready"] is False


def test_continuous_extraction_metadata_includes_selected_source() -> None:
    from coil_win_app.core_adapter import build_target_config, run_continuous_extraction

    config = build_target_config(
        modeling_input_mode="continuous_steady_state",
        freq_hz=1.0,
        cycle_count=1.5,
        target_peak_field_mT=50.0,
    )
    source = {"filename": "continuous_sine_1Hz.csv", "path": "C:/data/continuous_sine_1Hz.csv", "category": "continuous"}
    result = run_continuous_extraction(config, source)

    assert result.status == "not_connected"
    assert result.metadata["adapter_input_contract_ready"] is True
    assert result.metadata["selected_source_filename"] == "continuous_sine_1Hz.csv"
    assert result.metadata["required_core_api"]


def test_second_modeling_missing_actual_drive_source_is_explicit() -> None:
    from coil_win_app.core_adapter import ModelingResult, run_finite_second_modeling

    first_result = ModelingResult(status="not_connected", metadata={}, warnings=[])
    result = run_finite_second_modeling(_target_config(), first_result, {})

    assert result.status == "missing_actual_drive_source"
    assert result.metadata["adapter_input_contract_ready"] is False
