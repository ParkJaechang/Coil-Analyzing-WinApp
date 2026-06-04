from __future__ import annotations

import pandas as pd


def test_finite_page_metadata_formatter_handles_missing_keys() -> None:
    from coil_win_app.core_adapter import ModelingResult
    from coil_win_app.ui.finite_modeling_page import _format_finite_first_metadata

    result = ModelingResult(
        status="ok",
        metadata={},
        warnings=[],
        command_profile=pd.DataFrame({"time_s": [0.0], "limited_voltage_v": [0.0]}),
    )

    lines = _format_finite_first_metadata(result)

    assert any(line == "field_per_volt_mT_per_v=not available" for line in lines)
    assert any(line == "positive_peak_error_ratio=not available" for line in lines)
    assert any(line == "clipping_fraction=not available" for line in lines)
