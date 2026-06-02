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
        return pd.DataFrame({"time_s": command_profile["time_s"], "limited_voltage_v": [0.0, 2.0]})

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
    assert result.metadata["selected_source_filename"] == path.name
    assert result.command_profile is not None
    assert list(result.command_profile.columns) == ["time_s", "limited_voltage_v"]
    assert calls["kwargs"]["freq_hz"] == 1.0
    assert calls["kwargs"]["cycle_count"] == 1.0
    assert export.status == "ok"
    assert list(export.export_frame.columns) == ["sample_index", "time_s", "voltage_v"]


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
