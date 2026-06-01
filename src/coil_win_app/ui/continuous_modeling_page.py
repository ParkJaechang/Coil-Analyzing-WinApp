from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from coil_win_app.core_adapter import run_continuous_extraction, run_continuous_first_modeling
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
        output.setPlainText(_format_result("continuous extraction", result.status, result.error_reason))

    def run_first_clicked() -> None:
        if state.target_config is None:
            output.setPlainText("Target Config를 먼저 설정하십시오.")
            return
        extraction = run_continuous_extraction(state.target_config, state.selected_continuous_source or {})
        result = run_continuous_first_modeling(state.target_config, extraction)
        state.latest_continuous_first_result = result
        output.setPlainText(_format_result("continuous first modeling", result.status, result.error_reason))

    run_extract.clicked.connect(run_extract_clicked)
    run_first.clicked.connect(run_first_clicked)
    run_second.clicked.connect(lambda: output.setPlainText("continuous second modeling: core adapter not_connected"))
    layout.addWidget(QLabel("Continuous production: steady-state 1cycle repeated output only."))
    layout.addWidget(run_extract)
    layout.addWidget(run_first)
    layout.addWidget(run_second)
    layout.addWidget(output)
    return widget


def _format_result(label: str, status: str, error_reason: str | None) -> str:
    return f"{label}: status={status}\nerror_reason={error_reason or 'none'}"
