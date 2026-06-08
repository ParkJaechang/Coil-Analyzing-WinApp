from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication, QFileDialog, QComboBox, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from coil_win_app.core_adapter import load_project_sources, preview_source_file, read_source_dataframe
from coil_win_app.core_dependency import configure_core_path, get_core_dependency_status, build_runtime_diagnostic_packet
from coil_win_app.finite_source_schema import build_finite_first_source_schema_report
from coil_win_app.project_state import ProjectState
from coil_win_app.runtime_diagnostics import build_core_status_summary, format_runtime_diagnostic_packet

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
    diagnostic_box = QTextEdit()
    diagnostic_box.setReadOnly(True)
    diagnostic_box.setStyleSheet(_TEXT_BOX_STYLE)
    schema_box = QTextEdit()
    schema_box.setReadOnly(True)
    schema_box.setStyleSheet(_TEXT_BOX_STYLE)
    event_box = QTextEdit()
    event_box.setReadOnly(True)
    event_box.setStyleSheet(_TEXT_BOX_STYLE)
    core_status = _info_label(_format_core_status())
    core_status_summary = _selected_label_widget(_format_core_status_summary())

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
    data_button = QPushButton("Choose Data Folder")
    preview_button = QPushButton("Preview selected source")
    row.addWidget(project_button)
    row.addWidget(data_button)
    layout.addLayout(row)
    layout.addWidget(_section_title("CORE STATUS"))
    layout.addWidget(core_status_summary)
    layout.addWidget(core_status)
    core_button = QPushButton("Choose Core Source Folder")
    layout.addWidget(core_button)
    layout.addWidget(_section_title("RUNTIME DIAGNOSTICS"))
    runtime_row = QHBoxLayout()
    diagnostic_button = QPushButton("Show Runtime Diagnostic Packet")
    copy_diagnostic_button = QPushButton("Copy Runtime Diagnostic Packet to Clipboard")
    runtime_row.addWidget(diagnostic_button)
    runtime_row.addWidget(copy_diagnostic_button)
    layout.addLayout(runtime_row)
    layout.addWidget(diagnostic_box)
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
    layout.addWidget(_section_title("FINITE SOURCE SCHEMA REPORT"))
    schema_button = QPushButton("Check selected finite source schema")
    layout.addWidget(schema_button)
    layout.addWidget(schema_box)
    layout.addWidget(_section_title("RECENT EVENTS"))
    layout.addWidget(event_box)

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

    def choose_core_folder() -> None:
        folder = QFileDialog.getExistingDirectory(widget, "Choose Streamlit core repo root or src folder")
        if not folder:
            return
        result = configure_core_path(folder)
        if result["status"] == "ok":
            state.set_core_src_path(result["added_sys_path"])
        else:
            state.add_status(f"core path failed: {result['core_import_error']}")
        core_status.setText(_format_core_status())
        core_status_summary.setText(_format_core_status_summary())
        _refresh_event_log(state, event_box)

    def show_runtime_diagnostic_packet() -> str:
        packet = build_runtime_diagnostic_packet()
        text = format_runtime_diagnostic_packet(packet)
        diagnostic_box.setPlainText(text)
        state.add_status("runtime diagnostic packet shown")
        _refresh_event_log(state, event_box)
        return text

    def copy_runtime_diagnostic_packet() -> None:
        text = show_runtime_diagnostic_packet()
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)
            state.add_status("runtime diagnostic packet copied to clipboard")
            _refresh_event_log(state, event_box)

    def choose_data_folder() -> None:
        folder = QFileDialog.getExistingDirectory(widget, "Choose data folder")
        if not folder:
            return
        state.set_data_path(folder)
        data_label.setText(f"Data folder: {folder}")
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

    def check_selected_finite_schema() -> None:
        result = read_source_dataframe(state.selected_finite_source or {})
        if result.status != "ok" or result.command_profile is None:
            schema_box.setPlainText(f"schema report unavailable: status={result.status}; error={result.error_reason or 'unknown'}")
            state.add_status("finite schema check failed")
            _refresh_event_log(state, event_box)
            return
        report = build_finite_first_source_schema_report(result.command_profile)
        schema_box.setPlainText(_format_schema_report(report))
        state.add_status("finite schema checked")
        _refresh_event_log(state, event_box)

    project_button.clicked.connect(choose_project_folder)
    core_button.clicked.connect(choose_core_folder)
    diagnostic_button.clicked.connect(show_runtime_diagnostic_packet)
    copy_diagnostic_button.clicked.connect(copy_runtime_diagnostic_packet)
    data_button.clicked.connect(choose_data_folder)
    finite_combo.currentIndexChanged.connect(update_finite_selection)
    continuous_combo.currentIndexChanged.connect(update_continuous_selection)
    actual_drive_combo.currentIndexChanged.connect(update_actual_drive_selection)
    preview_button.clicked.connect(preview_selected_source)
    schema_button.clicked.connect(check_selected_finite_schema)
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
    state.add_status(f"source scan completed: {len(records)} files")
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
    return "{filename} | category={category} | reason={reason} | suffix={suffix} | size={size}".format(
        filename=record.get("filename", ""),
        category=record.get("category", "unknown"),
        reason=record.get("reason", "unknown"),
        suffix=record.get("suffix", ""),
        size=record.get("file_size_bytes", "unknown"),
    )


def _selected_label(label: str, record: dict[str, Any] | None) -> str:
    filename = record.get("filename", "none") if record else "none"
    return f"{label}: {filename}"


def _format_core_status() -> str:
    return _format_core_status_from_dependency(get_core_dependency_status())


def _format_core_status_summary() -> str:
    summary = build_core_status_summary(get_core_dependency_status())
    return (
        "severity={severity} | {headline} | blocking_reason={blocking}"
    ).format(
        severity=summary["severity"],
        headline=summary["headline"],
        blocking=summary["blocking_reason"] or "none",
    )


def _format_core_status_from_dependency(status: dict[str, Any]) -> str:
    configured_path = status.get("configured_core_path") or status.get("added_sys_path") or "none"
    missing_finite = status.get("missing_finite_first_modules") or []
    missing_optional = status.get("missing_optional_workflow_modules") or []
    forbidden = status.get("forbidden_module_status") or {}
    forbidden_loaded = sorted(name for name, item in forbidden.items() if isinstance(item, dict) and item.get("loaded"))
    return (
        "core dependency: "
        f"core path configured={_yes_no(status.get('core_path_configured'))} | "
        f"core package available={_yes_no(status.get('core_package_import_available'))} | "
        f"finite first core available={_yes_no(status.get('finite_first_core_available'))} | "
        f"finite first API available={_yes_no(status.get('finite_first_api_available'))} | "
        f"expected SHA={status.get('core_sha')} | "
        f"actual SHA={status.get('actual_core_sha') or 'unknown'} | "
        f"SHA match={_match_label(status.get('actual_core_sha_matches_expected'))} | "
        f"configured path={configured_path} | "
        f"missing finite first modules={_join_or_none(missing_finite)} | "
        f"missing optional workflow modules={_join_or_none(missing_optional)} | "
        f"api missing reason={status.get('api_missing_reason') or 'none'} | "
        f"streamlit imported={_yes_no(status.get('streamlit_imported'))} | "
        f"forbidden loaded={_join_or_none(forbidden_loaded)}"
    )


def _yes_no(value: Any) -> str:
    return "yes" if bool(value) else "no"


def _match_label(value: Any) -> str:
    if value is None:
        return "unknown"
    return "yes" if bool(value) else "no"


def _join_or_none(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def _format_schema_report(report: dict[str, Any]) -> str:
    lines = [
        f"status={report.get('status')}",
        f"row_count={report.get('row_count')}",
        "missing_column_groups=" + _join_or_none(list(report.get("missing_column_groups") or [])),
        f"resolved_columns={report.get('resolved_columns')}",
        f"prepared_columns={report.get('prepared_columns')}",
        f"numeric_finite_counts={report.get('numeric_finite_counts')}",
        f"final_lut_input_rejected={report.get('final_lut_input_rejected')}",
        f"rejected_reason={report.get('rejected_reason') or 'none'}",
        f"required_column_candidates={report.get('required_column_candidates')}",
    ]
    return "\n".join(lines)


def _refresh_event_log(state: ProjectState, event_box: QTextEdit) -> None:
    messages = state.status_messages or []
    event_box.setPlainText("\n".join(messages[-20:]) if messages else "no events")


_TEXT_BOX_STYLE = """
QTextEdit {
    color: #e5e7eb;
    font-family: Consolas;
    font-size: 12px;
}
"""


def _section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(_card_label_style(color="#93c5fd", font_size=16, font_weight=700))
    return label


def _subsection_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(_card_label_style(color="#cbd5e1", font_size=13, font_weight=700))
    return label


def _info_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(_card_label_style(color="#e5e7eb", font_size=12, font_weight=400))
    return label


def _selected_label_widget(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(_card_label_style(color="#86efac", font_size=12, font_weight=700))
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
