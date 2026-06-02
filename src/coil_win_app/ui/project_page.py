from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QFileDialog, QComboBox, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from coil_win_app.core_adapter import load_project_sources, preview_source_file
from coil_win_app.core_dependency import get_core_dependency_status
from coil_win_app.project_state import ProjectState


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPO_ROOT / "Data"
SECOND_RESULT_DIR = DEFAULT_DATA_DIR / "Second_Result"


def create_project_page(state: ProjectState) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    project_label = _info_label("Project folder: not selected")
    data_label = _info_label("Data folder: not selected")
    source_count_label = _info_label("finite: 0 / continuous: 0 / actual-drive: 0 / unknown: 0")
    source_list = QTextEdit()
    source_list.setReadOnly(True)
    source_list.setStyleSheet(_TEXT_BOX_STYLE)
    preview_box = QTextEdit()
    preview_box.setReadOnly(True)
    preview_box.setStyleSheet(_TEXT_BOX_STYLE)
    core_status = _info_label(_format_core_status())

    finite_combo = QComboBox()
    continuous_combo = QComboBox()
    actual_drive_combo = QComboBox()
    selected_finite_label = _selected_label_widget("selected finite source: none")
    selected_continuous_label = _selected_label_widget("selected continuous source: none")
    selected_actual_drive_label = _selected_label_widget("selected actual-drive source: none")

    layout.addWidget(_section_title("PROJECT / DATA"))
    layout.addWidget(_info_label("Select project and data folders. Files are not modified or deleted."))
    layout.addWidget(project_label)
    layout.addWidget(data_label)

    row = QHBoxLayout()
    project_button = QPushButton("Choose Project Folder")
    data_button = QPushButton("Connect Default Data Folder")
    preview_button = QPushButton("Preview selected source")
    row.addWidget(project_button)
    row.addWidget(data_button)
    layout.addLayout(row)
    layout.addWidget(_section_title("CORE STATUS"))
    layout.addWidget(core_status)
    layout.addWidget(_section_title("SOURCE INVENTORY"))
    layout.addWidget(source_count_label)
    layout.addWidget(_section_title("SOURCE SELECTION"))
    layout.addWidget(_subsection_title("Finite source"))
    layout.addWidget(finite_combo)
    layout.addWidget(selected_finite_label)
    layout.addWidget(_subsection_title("Continuous source"))
    layout.addWidget(continuous_combo)
    layout.addWidget(selected_continuous_label)
    layout.addWidget(_subsection_title("Actual-drive source"))
    layout.addWidget(actual_drive_combo)
    layout.addWidget(selected_actual_drive_label)
    layout.addWidget(_subsection_title("Full source list / unknown source list"))
    layout.addWidget(source_list)
    layout.addWidget(_section_title("SOURCE PREVIEW"))
    layout.addWidget(preview_button)
    layout.addWidget(preview_box)

    def choose_project_folder() -> None:
        folder = QFileDialog.getExistingDirectory(widget, "Choose project folder")
        if folder:
            state.set_project_path(folder)
            project_label.setText(f"Project folder: {folder}")
            _refresh_sources(
                Path(folder),
                source_count_label,
                source_list,
                finite_combo,
                continuous_combo,
                actual_drive_combo,
                selected_finite_label,
                selected_continuous_label,
                selected_actual_drive_label,
                state,
            )

    def connect_default_data_folder() -> None:
        DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
        second_result = ensure_second_result_folder(DEFAULT_DATA_DIR)
        state.set_data_path(DEFAULT_DATA_DIR)
        data_label.setText(f"Data folder: {DEFAULT_DATA_DIR} | second result folder: {second_result.name}")
        _refresh_sources(
            DEFAULT_DATA_DIR,
            source_count_label,
            source_list,
            finite_combo,
            continuous_combo,
            actual_drive_combo,
            selected_finite_label,
            selected_continuous_label,
            selected_actual_drive_label,
            state,
        )

    def update_finite_selection(index: int) -> None:
        state.selected_finite_source = _combo_record(finite_combo, index)
        selected_finite_label.setText(_selected_label("selected finite source", state.selected_finite_source))

    def update_continuous_selection(index: int) -> None:
        state.selected_continuous_source = _combo_record(continuous_combo, index)
        selected_continuous_label.setText(_selected_label("selected continuous source", state.selected_continuous_source))

    def update_actual_drive_selection(index: int) -> None:
        state.selected_actual_drive_source = _combo_record(actual_drive_combo, index)
        selected_actual_drive_label.setText(_selected_label("selected actual-drive source", state.selected_actual_drive_source))

    def preview_selected_source() -> None:
        record = state.selected_finite_source or state.selected_continuous_source or state.selected_actual_drive_source
        result = preview_source_file(record or {})
        if result.status != "ok" or result.export_frame is None:
            preview_box.setPlainText(f"source preview failed: status={result.status}; error={result.error_reason or 'unknown'}")
            return
        preview_box.setPlainText(
            "source preview: {filename} | rows={rows} | columns={columns}\n\n{table}".format(
                filename=result.metadata.get("source_filename", "unknown"),
                rows=result.metadata.get("row_count_estimate", "unknown"),
                columns=", ".join(result.metadata.get("columns", [])),
                table=result.export_frame.to_string(index=False),
            )
        )

    project_button.clicked.connect(choose_project_folder)
    data_button.clicked.connect(connect_default_data_folder)
    finite_combo.currentIndexChanged.connect(update_finite_selection)
    continuous_combo.currentIndexChanged.connect(update_continuous_selection)
    actual_drive_combo.currentIndexChanged.connect(update_actual_drive_selection)
    preview_button.clicked.connect(preview_selected_source)
    return widget


def _refresh_sources(
    root: Path,
    count_label: QLabel,
    source_list: QTextEdit,
    finite_combo: QComboBox,
    continuous_combo: QComboBox,
    actual_drive_combo: QComboBox,
    selected_finite_label: QLabel,
    selected_continuous_label: QLabel,
    selected_actual_drive_label: QLabel,
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
    selected_finite_label.setText(_selected_label("selected finite source", state.selected_finite_source))
    selected_continuous_label.setText(_selected_label("selected continuous source", state.selected_continuous_source))
    selected_actual_drive_label.setText(_selected_label("selected actual-drive source", state.selected_actual_drive_source))
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


def _selected_label(label: str, record: dict[str, Any] | None) -> str:
    filename = record.get("filename", "none") if record else "none"
    return f"{label}: {filename}"


def _format_core_status() -> str:
    status = get_core_dependency_status()
    state = "available" if status["core_import_available"] else "not_connected"
    return f"core dependency: {state} | checked={len(status['core_modules_checked'])}"


def ensure_second_result_folder(data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    second_result_dir = data_dir / "Second_Result"
    second_result_dir.mkdir(parents=True, exist_ok=True)
    return second_result_dir


_TEXT_BOX_STYLE = """
QTextEdit {
    color: #1f2933;
    font-family: Consolas;
    font-size: 12px;
}
"""


def _section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(_card_label_style(color="#2563eb", font_size=16, font_weight=700))
    return label


def _subsection_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(_card_label_style(color="#475569", font_size=13, font_weight=700))
    return label


def _info_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(_card_label_style(color="#111827", font_size=12, font_weight=400))
    return label


def _selected_label_widget(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(_card_label_style(color="#059669", font_size=12, font_weight=700))
    return label


def _card_label_style(*, color: str, font_size: int, font_weight: int) -> str:
    return f"""
        QLabel {{
            color: {color};
            padding: 4px 6px;
            font-size: {font_size}px;
            font-weight: {font_weight};
        }}
        """
