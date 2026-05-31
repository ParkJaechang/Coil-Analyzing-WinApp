from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from coil_win_app.core_adapter import load_project_sources
from coil_win_app.project_state import ProjectState


def create_project_page(state: ProjectState) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    project_label = QLabel("Project folder: not selected")
    data_label = QLabel("Data folder: not selected")
    source_count_label = QLabel("finite: 0 / continuous: 0 / actual-drive: 0 / unknown: 0")

    layout.addWidget(QLabel("Select project and data folders. Files are not modified or deleted."))
    layout.addWidget(project_label)
    layout.addWidget(data_label)

    row = QHBoxLayout()
    project_button = QPushButton("Choose Project Folder")
    data_button = QPushButton("Choose Data Folder")
    row.addWidget(project_button)
    row.addWidget(data_button)
    layout.addLayout(row)
    layout.addWidget(source_count_label)

    def choose_project_folder() -> None:
        folder = QFileDialog.getExistingDirectory(widget, "Choose project folder")
        if folder:
            state.set_project_path(folder)
            project_label.setText(f"Project folder: {folder}")
            _refresh_source_counts(Path(folder), source_count_label)

    def choose_data_folder() -> None:
        folder = QFileDialog.getExistingDirectory(widget, "Choose data folder")
        if folder:
            state.set_data_path(folder)
            data_label.setText(f"Data folder: {folder}")
            _refresh_source_counts(Path(folder), source_count_label)

    project_button.clicked.connect(choose_project_folder)
    data_button.clicked.connect(choose_data_folder)
    return widget


def _refresh_source_counts(root: Path, label: QLabel) -> None:
    result = load_project_sources(root)
    counts = result.metadata.get("source_counts", {}) if result.status == "ok" else {}
    label.setText(
        "finite: {finite} / continuous: {continuous} / actual-drive: {actual_drive} / unknown: {unknown}".format(
            finite=counts.get("finite", 0),
            continuous=counts.get("continuous", 0),
            actual_drive=counts.get("actual_drive", 0),
            unknown=counts.get("unknown", 0),
        )
    )
