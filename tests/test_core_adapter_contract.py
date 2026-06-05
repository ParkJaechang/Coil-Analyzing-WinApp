from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def test_package_and_core_adapter_import_without_streamlit() -> None:
    package = importlib.import_module("coil_win_app")
    adapter = importlib.import_module("coil_win_app.core_adapter")

    assert package is not None
    assert adapter is not None
    assert "streamlit" not in adapter.__dict__


def test_target_config_keeps_user_peak_and_voltage_policy() -> None:
    from coil_win_app.core_adapter import build_target_config

    config = build_target_config(
        modeling_input_mode="finite_startup_aware",
        freq_hz=1.25,
        cycle_count=1.5,
        target_peak_field_mT=72.5,
        source_waveform_family="sine",
    )

    assert config.target_shape == "fixed_rounded_triangle"
    assert config.target_peak_field_mT == 72.5
    assert config.field_normalization_mode == "target_peak"
    assert config.voltage_limit_v == 10.0


def test_finite_and_continuous_cycle_policy() -> None:
    from coil_win_app.core_adapter import build_target_config

    finite = build_target_config(
        modeling_input_mode="finite_startup_aware",
        freq_hz=1.0,
        cycle_count=1.0,
        target_peak_field_mT=50.0,
    )
    continuous = build_target_config(
        modeling_input_mode="continuous_steady_state",
        freq_hz=1.0,
        cycle_count=1.5,
        target_peak_field_mT=50.0,
    )

    assert finite.cycle_count in (1.0, 1.5)
    assert continuous.cycle_count == 1.0

    with pytest.raises(ValueError, match="finite production cycles"):
        build_target_config(
            modeling_input_mode="finite_startup_aware",
            freq_hz=1.0,
            cycle_count=1.25,
            target_peak_field_mT=50.0,
        )


def test_source_metadata_does_not_overwrite_target_config() -> None:
    from coil_win_app.core_adapter import build_target_config

    config = build_target_config(
        modeling_input_mode="finite_startup_aware",
        freq_hz=2.0,
        cycle_count=1.0,
        target_peak_field_mT=88.0,
        source_waveform_family="triangle",
        source_metadata={"target_peak_field_mT": 25.0, "cycle_count": 1.5},
    )

    assert config.target_peak_field_mT == 88.0
    assert config.cycle_count == 1.0


def test_missing_core_dependency_returns_explicit_not_connected(tmp_path) -> None:
    from coil_win_app.core_adapter import build_target_config, run_finite_first_modeling

    source = tmp_path / "finite_sine_1Hz.csv"
    source.write_text("time_s,limited_voltage_v,HallBz,target_field_mT\n0,0,0,0\n", encoding="utf-8")
    config = build_target_config(
        modeling_input_mode="finite_startup_aware",
        freq_hz=1.0,
        cycle_count=1.0,
        target_peak_field_mT=50.0,
    )
    result = run_finite_first_modeling(
        config,
        source_selection={"path": str(source), "filename": source.name, "category": "finite"},
    )

    assert result.status == "not_connected"
    assert result.error_reason
    assert result.command_profile is None


def test_streamlit_dependency_sha_is_documented() -> None:
    from coil_win_app.core_adapter import CORE_SHA

    doc = Path("docs/winapp_core_dependency.md").read_text(encoding="utf-8")

    assert CORE_SHA == "b3c1103825c9c30f2db9ea14153959ffc2fe300e"
    assert "STREAMLIT_CORE_REPO=ParkJaechang/Coil-Analyzing" in doc
    assert f"STREAMLIT_CORE_SHA={CORE_SHA}" in doc


def test_get_core_version_includes_dependency_status() -> None:
    from coil_win_app.core_adapter import get_core_version

    version = get_core_version()

    assert "core_sha" in version
    assert "core_repo" in version
    assert "adapter_status" in version
    assert "core_import_available" in version
