from __future__ import annotations

from pathlib import Path


def test_default_data_folder_points_to_repo_data() -> None:
    from coil_win_app.ui.project_page import DEFAULT_DATA_DIR, SECOND_RESULT_DIR

    repo_root = Path.cwd()

    assert DEFAULT_DATA_DIR == repo_root / "Data"
    assert SECOND_RESULT_DIR == DEFAULT_DATA_DIR / "Second_Result"


def test_second_result_folder_helper_creates_folder(tmp_path) -> None:
    from coil_win_app.ui.project_page import ensure_second_result_folder

    result = ensure_second_result_folder(tmp_path)

    assert result == tmp_path / "Second_Result"
    assert result.is_dir()


def test_project_page_uses_default_data_folder_button() -> None:
    source = Path("src/coil_win_app/ui/project_page.py").read_text(encoding="utf-8")

    assert "DEFAULT_DATA_DIR" in source
    assert "ensure_second_result_folder" in source
    assert "connect_default_data_folder" in source
    assert "QFileDialog.getExistingDirectory(widget, \"Choose data folder\")" not in source
