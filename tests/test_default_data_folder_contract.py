from __future__ import annotations

from pathlib import Path

def test_project_page_does_not_create_repo_root_data_folder() -> None:
    source = Path("src/coil_win_app/ui/project_page.py").read_text(encoding="utf-8")

    assert "Connect Default Data Folder" not in source
    assert "ensure_second_result_folder" not in source
    assert "mkdir(parents=True" not in source
    assert 'QFileDialog.getExistingDirectory(widget, "Choose data folder")' in source
