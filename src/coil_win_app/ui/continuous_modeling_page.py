from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from coil_win_app.core_adapter import (
    ModelingResult,
    TargetConfig,
    run_continuous_extraction,
    run_continuous_first_modeling,
)
from coil_win_app.project_state import ProjectState


def create_continuous_modeling_page(state: ProjectState) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    output = QTextEdit()
    output.setReadOnly(True)
    run_extract = QPushButton("Run steady-state 1cycle extraction")
    run_first = QPushButton("Run continuous first modeling")
    run_second = QPushButton("Run continuous second correction")

    def run_extract_clicked() -> None:
        if state.target_config is None:
            output.setPlainText("Target Config를 먼저 설정하십시오.")
            return
        result = run_continuous_extraction(state.target_config, state.selected_continuous_source or {})
        output.setPlainText(
            "\n".join(
                [
                    _format_config_summary(state.target_config),
                    _format_source_summary("Selected continuous source", state.selected_continuous_source),
                    _format_result("continuous extraction", result),
                ]
            )
        )

    def run_first_clicked() -> None:
        if state.target_config is None:
            output.setPlainText("Target Config를 먼저 설정하십시오.")
            return
        extraction = run_continuous_extraction(state.target_config, state.selected_continuous_source or {})
        result = run_continuous_first_modeling(state.target_config, extraction)
        state.latest_continuous_first_result = result
        output.setPlainText(
            "\n".join(
                [
                    _format_config_summary(state.target_config),
                    _format_source_summary("Selected continuous source", state.selected_continuous_source),
                    _format_result("continuous first modeling", result),
                ]
            )
        )

    run_extract.clicked.connect(run_extract_clicked)
    run_first.clicked.connect(run_first_clicked)
    run_second.clicked.connect(lambda: output.setPlainText("continuous second modeling: core adapter not_connected"))
    layout.addWidget(QLabel("Continuous production: steady-state 1cycle repeated output only."))
    layout.addWidget(QLabel("Selected continuous source is read from Project / Data."))
    layout.addWidget(run_extract)
    layout.addWidget(run_first)
    layout.addWidget(run_second)
    layout.addWidget(output)
    return widget


def _format_config_summary(config: TargetConfig) -> str:
    return (
        "TargetConfig: mode={mode} | freq_hz={freq:g} | cycle_count={cycle:g} | "
        "target_peak_field_mT={peak:g} | voltage_limit_v={limit:g}"
    ).format(
        mode=config.modeling_input_mode,
        freq=config.freq_hz,
        cycle=config.cycle_count,
        peak=config.target_peak_field_mT,
        limit=config.voltage_limit_v,
    )


def _format_source_summary(label: str, record: dict[str, Any] | None) -> str:
    if not record:
        return f"{label}: not selected"
    return f"{label}: filename={record.get('filename', 'unknown')} | category={record.get('category', 'unknown')}"


def _format_result(label: str, result: ModelingResult) -> str:
    selected = result.metadata.get("selected_source_filename", "not selected")
    return (
        f"{label}: status={result.status}\n"
        f"error_reason={result.error_reason or 'none'}\n"
        f"source filename={selected}"
    )
