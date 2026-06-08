from __future__ import annotations

import sys
import types
from pathlib import Path

import pandas as pd


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "finite_first_minimal.csv"


def _target_config():
    from coil_win_app.core_adapter import build_target_config

    return build_target_config(
        modeling_input_mode="finite_startup_aware",
        freq_hz=1.0,
        cycle_count=1.0,
        target_peak_field_mT=50.0,
    )


def _source_record() -> dict[str, str]:
    return {"path": str(FIXTURE), "filename": FIXTURE.name, "category": "finite"}


def test_fixture_finite_source_schema_reaches_core_dependency_boundary() -> None:
    from coil_win_app.core_adapter import run_finite_first_modeling

    result = run_finite_first_modeling(_target_config(), _source_record())

    assert result.status in {"not_connected", "ok"}
    assert result.status != "schema_unavailable"
    assert result.metadata.get("selected_source_filename") == FIXTURE.name


def test_fixture_finite_source_fake_core_exports_final_lut(monkeypatch) -> None:
    from coil_win_app.core_adapter import build_final_lut_export, run_finite_first_modeling

    module = types.ModuleType("field_analysis.finite_first_phase_sync")

    def apply_finite_first_phase_sync_modeling(command_profile, **_kwargs):
        return {
            "status": "ok",
            "metadata": {
                "finite_first_modeling_status": "ok",
                "field_per_volt_mT_per_v": 8.0,
                "residual_to_voltage_conversion_basis": "field_per_volt_response",
            },
            "command_profile": pd.DataFrame(
                {
                    "time_s": command_profile["time_s"],
                    "limited_voltage_v": command_profile["limited_voltage_v"],
                }
            ),
        }

    module.apply_finite_first_phase_sync_modeling = apply_finite_first_phase_sync_modeling
    monkeypatch.setitem(sys.modules, "field_analysis", types.ModuleType("field_analysis"))
    monkeypatch.setitem(sys.modules, "field_analysis.finite_first_phase_sync", module)

    result = run_finite_first_modeling(_target_config(), _source_record())
    export = build_final_lut_export(result)

    assert result.status == "ok"
    assert result.metadata["core_bridge_used"] is True
    assert export.status == "ok"
    assert list(export.export_frame.columns) == ["sample_index", "time_s", "voltage_v"]
    assert export.metadata["fourier_resynthesis"] is False
