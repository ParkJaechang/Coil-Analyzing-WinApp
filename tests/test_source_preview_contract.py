from __future__ import annotations


def test_preview_source_file_reads_small_csv(tmp_path) -> None:
    from coil_win_app.core_adapter import preview_source_file

    path = tmp_path / "finite_sine_1Hz.csv"
    path.write_text("time_s,voltage_v\n0.0,0.0\n0.1,1.0\n", encoding="utf-8")
    record = {"path": str(path), "filename": path.name, "category": "finite"}

    result = preview_source_file(record, max_rows=1)

    assert result.status == "ok"
    assert result.metadata["source_filename"] == path.name
    assert result.metadata["source_category"] == "finite"
    assert result.metadata["columns"] == ["time_s", "voltage_v"]
    assert result.metadata["row_count_estimate"] == 2
    assert result.metadata["preview_row_count"] == 1
    assert result.metadata["result_kind"] == "source_preview"
    assert result.command_profile is None
    assert result.export_frame is not None
    assert list(result.export_frame.columns) == ["time_s", "voltage_v"]


def test_preview_source_file_reports_unsupported_file_type(tmp_path) -> None:
    from coil_win_app.core_adapter import preview_source_file

    path = tmp_path / "finite_data.xlsx"
    path.write_text("not csv", encoding="utf-8")

    result = preview_source_file({"path": str(path), "filename": path.name, "category": "finite"})

    assert result.status == "failed"
    assert "unsupported file type" in str(result.error_reason)


def test_preview_source_file_missing_source_is_explicit() -> None:
    from coil_win_app.core_adapter import preview_source_file

    result = preview_source_file({})

    assert result.status == "missing_source"
    assert result.error_reason


def test_final_export_rejects_source_preview_result(tmp_path) -> None:
    from coil_win_app.core_adapter import build_final_lut_export, preview_source_file

    path = tmp_path / "finite_sine_1Hz.csv"
    path.write_text("time_s,limited_voltage_v\n0.0,0.0\n", encoding="utf-8")
    preview = preview_source_file({"path": str(path), "filename": path.name, "category": "finite"})

    export = build_final_lut_export(preview)

    assert export.status == "failed"
    assert "source preview" in str(export.error_reason)
