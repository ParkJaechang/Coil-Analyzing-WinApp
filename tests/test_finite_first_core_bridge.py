from __future__ import annotations

import sys
import types

import pandas as pd


def _target_config():
    from coil_win_app.core_adapter import build_target_config

    return build_target_config(
        modeling_input_mode="finite_startup_aware",
        freq_hz=1.0,
        cycle_count=1.0,
        target_peak_field_mT=50.0,
    )


def test_read_source_dataframe_reads_csv(tmp_path) -> None:
    from coil_win_app.core_adapter import read_source_dataframe

    path = tmp_path / "finite_sine_1Hz.csv"
    path.write_text("time_s,limited_voltage_v,HallBz,physical_target_output_mT\n0,0,0,0\n", encoding="utf-8")

    result = read_source_dataframe({"path": str(path), "filename": path.name, "category": "finite"})

    assert result.status == "ok"
    assert result.metadata["filename"] == path.name
    assert result.metadata["row_count"] == 1
    assert result.metadata["columns"] == ["time_s", "limited_voltage_v", "HallBz", "physical_target_output_mT"]
    assert result.command_profile is not None


def test_finite_first_bridge_calls_fake_core_and_exports(tmp_path, monkeypatch) -> None:
    from coil_win_app.core_adapter import build_final_lut_export, run_finite_first_modeling

    path = tmp_path / "finite_sine_1Hz.csv"
    path.write_text(
        "time_s,limited_voltage_v,HallBz,physical_target_output_mT\n"
        "0.0,0.0,0.0,0.0\n"
        "0.1,1.0,-10.0,10.0\n",
        encoding="utf-8",
    )
    calls: dict[str, object] = {}

    module = types.ModuleType("field_analysis.finite_first_phase_sync")

    def apply_finite_first_phase_sync_modeling(command_profile, **kwargs):
        calls["columns"] = list(command_profile.columns)
        calls["kwargs"] = kwargs
        return {
            "status": "ok",
            "metadata": {
                "finite_first_modeling_status": "ok",
                "phase_sync_method": "peak_pair_midpoint_to_target_zero_crossing",
                "phase_sync_alignment_anchor": "midpoint_to_zero_crossing",
                "phase_sync_peak_reference": "positive_negative_peak_pair",
                "phase_sync_midpoint_left_peak_time_s": 0.25,
                "phase_sync_midpoint_right_peak_time_s": 0.75,
                "phase_delay_s": 0.012,
                "measured_field_scale_to_target_mT": 1.2,
                "field_per_volt_mT_per_v": 8.5,
                "voltage_per_field_v_per_mT": 0.117647,
                "residual_to_voltage_conversion_basis": "field_per_volt_response",
                "correction_delta_mode": "residual_div_field_per_volt",
                "positive_peak_error_ratio": 0.03,
                "negative_peak_error_ratio": -0.02,
                "peak_to_peak_error_ratio": 0.01,
            },
            "command_profile": pd.DataFrame({"time_s": command_profile["time_s"], "limited_voltage_v": [0.0, 2.0]}),
        }

    module.apply_finite_first_phase_sync_modeling = apply_finite_first_phase_sync_modeling
    monkeypatch.setitem(sys.modules, "field_analysis", types.ModuleType("field_analysis"))
    monkeypatch.setitem(sys.modules, "field_analysis.finite_first_phase_sync", module)

    result = run_finite_first_modeling(
        _target_config(),
        {"path": str(path), "filename": path.name, "category": "finite"},
    )
    export = build_final_lut_export(result)

    assert result.status == "ok"
    assert result.metadata["core_bridge_used"] is True
    assert result.metadata["finite_first_bridge_version"] == "phase_synced_field_per_volt_aware"
    assert result.metadata["field_per_volt_mT_per_v"] == 8.5
    assert result.metadata["voltage_per_field_v_per_mT"] == 0.117647
    assert result.metadata["correction_delta_mode"] == "residual_div_field_per_volt"
    assert result.metadata["positive_peak_error_ratio"] == 0.03
    assert result.metadata["final_voltage_limit_v"] == 10.0
    assert result.metadata["selected_source_filename"] == path.name
    assert result.command_profile is not None
    assert list(result.command_profile.columns) == ["time_s", "limited_voltage_v"]
    assert calls["kwargs"]["freq_hz"] == 1.0
    assert calls["kwargs"]["cycle_count"] == 1.0
    assert export.status == "ok"
    assert list(export.export_frame.columns) == ["sample_index", "time_s", "voltage_v"]


def test_finite_first_metadata_key_contract() -> None:
    from coil_win_app.core_adapter import finite_first_optional_metadata_keys, finite_first_required_metadata_keys

    required = finite_first_required_metadata_keys()
    optional = finite_first_optional_metadata_keys()

    assert "field_per_volt_mT_per_v" in required
    assert "residual_to_voltage_conversion_basis" in required
    assert "correction_delta_mode" in required
    assert "final_voltage_limit_v" in required
    assert "phase_sync_peak_reference" in optional
    assert "phase_sync_midpoint_time_s" in optional
    assert "phase_sync_midpoint_left_peak_time_s" in optional
    assert "phase_sync_midpoint_right_peak_time_s" in optional
    assert "positive_peak_error_ratio" in optional


def test_finite_first_bridge_wraps_tuple_core_output(tmp_path, monkeypatch) -> None:
    from coil_win_app.core_adapter import run_finite_first_modeling

    path = tmp_path / "finite_sine_1Hz.csv"
    path.write_text("time_s,limited_voltage_v,HallBz,target_field_mT\n0,0,0,0\n", encoding="utf-8")
    module = types.ModuleType("field_analysis.finite_first_phase_sync")

    def apply_finite_first_phase_sync_modeling(command_profile, **_kwargs):
        return (
            pd.DataFrame({"time_s": command_profile["time_s"], "limited_voltage_v": [1.5]}),
            {"finite_first_modeling_status": "ok", "field_per_volt_mT_per_v": 7.0},
        )

    module.apply_finite_first_phase_sync_modeling = apply_finite_first_phase_sync_modeling
    monkeypatch.setitem(sys.modules, "field_analysis", types.ModuleType("field_analysis"))
    monkeypatch.setitem(sys.modules, "field_analysis.finite_first_phase_sync", module)

    result = run_finite_first_modeling(_target_config(), {"path": str(path), "filename": path.name, "category": "finite"})

    assert result.status == "ok"
    assert result.metadata["field_per_volt_mT_per_v"] == 7.0
    assert result.command_profile is not None
    assert result.command_profile["limited_voltage_v"].tolist() == [1.5]


def test_finite_first_bridge_schema_unavailable_blocks_core(tmp_path) -> None:
    from coil_win_app.core_adapter import run_finite_first_modeling

    path = tmp_path / "finite_bad.csv"
    path.write_text("time_s\n0.0\n", encoding="utf-8")

    result = run_finite_first_modeling(_target_config(), {"path": str(path), "filename": path.name, "category": "finite"})

    assert result.status == "schema_unavailable"
    assert "voltage" in result.metadata["missing_column_groups"]


def test_finite_first_bridge_core_exception_returns_failed(tmp_path, monkeypatch) -> None:
    from coil_win_app.core_adapter import run_finite_first_modeling

    path = tmp_path / "finite_sine_1Hz.csv"
    path.write_text("time_s,limited_voltage_v,HallBz,target_field_mT\n0,0,0,0\n", encoding="utf-8")
    module = types.ModuleType("field_analysis.finite_first_phase_sync")

    def apply_finite_first_phase_sync_modeling(_command_profile, **_kwargs):
        raise RuntimeError("fake core failure")

    module.apply_finite_first_phase_sync_modeling = apply_finite_first_phase_sync_modeling
    monkeypatch.setitem(sys.modules, "field_analysis", types.ModuleType("field_analysis"))
    monkeypatch.setitem(sys.modules, "field_analysis.finite_first_phase_sync", module)

    result = run_finite_first_modeling(_target_config(), {"path": str(path), "filename": path.name, "category": "finite"})

    assert result.status == "failed"
    assert "fake core failure" in str(result.error_reason)
    assert "streamlit" not in sys.modules
