from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QFileDialog, QComboBox, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from coil_win_app.core_adapter import load_project_sources
from coil_win_app.project_state import ProjectState


def create_project_page(state: ProjectState) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    project_label = QLabel("Project folder: not selected")
    data_label = QLabel("Data folder: not selected")
    source_count_label = QLabel("finite: 0 / continuous: 0 / actual-drive: 0 / unknown: 0")
    source_list = QTextEdit()
    source_list.setReadOnly(True)

    finite_combo = QComboBox()
    continuous_combo = QComboBox()
    actual_drive_combo = QComboBox()

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
    layout.addWidget(QLabel("finite source list"))
    layout.addWidget(finite_combo)
    layout.addWidget(QLabel("continuous source list"))
    layout.addWidget(continuous_combo)
    layout.addWidget(QLabel("actual-drive source list"))
    layout.addWidget(actual_drive_combo)
    layout.addWidget(QLabel("unknown source list"))
    layout.addWidget(source_list)

    def choose_project_folder() -> None:
        folder = QFileDialog.getExistingDirectory(widget, "Choose project folder")
        if folder:
            state.set_project_path(folder)
            project_label.setText(f"Project folder: {folder}")
            _refresh_sources(Path(folder), source_count_label, source_list, finite_combo, continuous_combo, actual_drive_combo, state)

    def choose_data_folder() -> None:
        folder = QFileDialog.getExistingDirectory(widget, "Choose data folder")
        if folder:
            state.set_data_path(folder)
            data_label.setText(f"Data folder: {folder}")
            _refresh_sources(Path(folder), source_count_label, source_list, finite_combo, continuous_combo, actual_drive_combo, state)

    def update_finite_selection(index: int) -> None:
        state.selected_finite_source = _combo_record(finite_combo, index)

    def update_continuous_selection(index: int) -> None:
        state.selected_continuous_source = _combo_record(continuous_combo, index)

    def update_actual_drive_selection(index: int) -> None:
        state.selected_actual_drive_source = _combo_record(actual_drive_combo, index)

    project_button.clicked.connect(choose_project_folder)
    data_button.clicked.connect(choose_data_folder)
    finite_combo.currentIndexChanged.connect(update_finite_selection)
    continuous_combo.currentIndexChanged.connect(update_continuous_selection)
    actual_drive_combo.currentIndexChanged.connect(update_actual_drive_selection)
    return widget


def _refresh_sources(
    root: Path,
    count_label: QLabel,
    source_list: QTextEdit,
    finite_combo: QComboBox,
    continuous_combo: QComboBox,
    actual_drive_combo: QComboBox,
    state: ProjectState,
) -> None:
    result = load_project_sources(root)
    if result.status != "ok":
        message = f"source scan failed: status={result.status}; error={result.error_reason or 'unknown'}"
        state.add_status(message)
        count_label.setText(message)
        source_list.setPlainText(message)
        return

    counts = result.metadata.get("source_counts", {})
    records = result.metadata.get("source_records", [])
    count_label.setText(
        "finite: {finite} / continuous: {continuous} / actual-drive: {actual_drive} / unknown: {unknown}".format(
            finite=counts.get("finite", 0),
            continuous=counts.get("continuous", 0),
            actual_drive=counts.get("actual_drive", 0),
            unknown=counts.get("unknown", 0),
        )
    )
    _populate_combo(finite_combo, records, "finite")
    _populate_combo(continuous_combo, records, "continuous")
    _populate_combo(actual_drive_combo, records, "actual_drive")
    state.selected_finite_source = _combo_record(finite_combo, finite_combo.currentIndex())
    state.selected_continuous_source = _combo_record(continuous_combo, continuous_combo.currentIndex())
    state.selected_actual_drive_source = _combo_record(actual_drive_combo, actual_drive_combo.currentIndex())
    source_list.setPlainText(_format_source_lists(records))


def _populate_combo(combo: QComboBox, records: list[dict[str, str]], category: str) -> None:
    combo.clear()
    combo.addItem("not selected", None)
    for record in records:
        if record.get("category") == category:
            combo.addItem(_record_label(record), record)


def _combo_record(combo: QComboBox, index: int) -> dict[str, Any] | None:
    if index < 0:
        return None
    value = combo.itemData(index)
    return value if isinstance(value, dict) else None


def _format_source_lists(records: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for category in ("finite", "continuous", "actual_drive", "unknown"):
        lines.append(f"{category}:")
        category_records = [record for record in records if record.get("category") == category]
        if not category_records:
            lines.append("  - none")
        for record in category_records:
            lines.append(f"  - {_record_label(record)} | path={record.get('path', '')}")
    return "\n".join(lines)


def _record_label(record: dict[str, str]) -> str:
    return "{filename} | category={category} | reason={reason}".format(
        filename=record.get("filename", ""),
        category=record.get("category", "unknown"),
        reason=record.get("reason", "unknown"),
    )
