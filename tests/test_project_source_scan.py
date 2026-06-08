from __future__ import annotations


def test_load_project_sources_returns_records_by_category(tmp_path) -> None:
    from coil_win_app.core_adapter import load_project_sources

    (tmp_path / "finite_sine_1Hz_1.0cycle.csv").write_text("t,v\n0,0\n", encoding="utf-8")
    (tmp_path / "continuous_triangle_2Hz.csv").write_text("t,v\n0,0\n", encoding="utf-8")
    (tmp_path / "abc123_finite_result_validation.csv").write_text("t,v\n0,0\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

    result = load_project_sources(tmp_path)

    assert result.status == "ok"
    assert result.metadata["source_counts"] == {
        "finite": 1,
        "continuous": 1,
        "actual_drive": 1,
        "unknown": 1,
    }
    records = result.metadata["source_records"]
    assert [record["filename"] for record in records] == [
        "abc123_finite_result_validation.csv",
        "continuous_triangle_2Hz.csv",
        "finite_sine_1Hz_1.0cycle.csv",
        "notes.txt",
    ]
    assert {record["category"] for record in records} == {"finite", "continuous", "actual_drive", "unknown"}
    reason_by_name = {record["filename"]: record["reason"] for record in records}
    assert reason_by_name["finite_sine_1Hz_1.0cycle.csv"] == "filename_pattern"
    assert reason_by_name["continuous_triangle_2Hz.csv"] == "filename_pattern"
    assert reason_by_name["abc123_finite_result_validation.csv"] == "keyword_match"
    assert reason_by_name["notes.txt"] == "unknown"
    finite_record = next(record for record in records if record["filename"] == "finite_sine_1Hz_1.0cycle.csv")
    assert finite_record["suffix"] == ".csv"
    assert int(finite_record["file_size_bytes"]) > 0


def test_source_category_inference_patterns(tmp_path) -> None:
    from coil_win_app.core_adapter import load_project_sources

    names = {
        "finite_triangle_5Hz_1.5cycle.csv": "finite",
        "sine_finite_support.csv": "finite",
        "continuous_sine_0.5Hz.csv": "continuous",
        "triangle_continuous_support.csv": "continuous",
        "drive_actual_result.csv": "actual_drive",
        "validation_run.csv": "actual_drive",
        "Transient_1st_Result.csv": "actual_drive",
        "Continuous_1st_Result.csv": "actual_drive",
        "misc.bin": "unknown",
    }
    for name in names:
        (tmp_path / name).write_text("x", encoding="utf-8")

    result = load_project_sources(tmp_path)
    by_name = {record["filename"]: record["category"] for record in result.metadata["source_records"]}

    assert by_name == names


def test_source_scan_reason_reflects_filename_or_keyword_match(tmp_path) -> None:
    from coil_win_app.core_adapter import load_project_sources

    (tmp_path / "finite_sine_1Hz.csv").write_text("x", encoding="utf-8")
    (tmp_path / "support_finite_sine_1Hz.csv").write_text("x", encoding="utf-8")
    (tmp_path / "Transient_1st_Result.csv").write_text("x", encoding="utf-8")
    (tmp_path / "unknown.txt").write_text("x", encoding="utf-8")

    result = load_project_sources(tmp_path)
    reason_by_name = {record["filename"]: record["reason"] for record in result.metadata["source_records"]}

    assert reason_by_name["finite_sine_1Hz.csv"] == "filename_pattern"
    assert reason_by_name["support_finite_sine_1Hz.csv"] == "keyword_match"
    assert reason_by_name["Transient_1st_Result.csv"] == "keyword_match"
    assert reason_by_name["unknown.txt"] == "unknown"
