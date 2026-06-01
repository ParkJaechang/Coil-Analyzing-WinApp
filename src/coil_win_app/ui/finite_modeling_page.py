from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from coil_win_app.core_adapter import run_finite_first_modeling, run_finite_second_modeling
from coil_win_app.project_state import ProjectState


def create_finite_modeling_page(state: ProjectState) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    output = QTextEdit()
    output.setReadOnly(True)
    run_first = QPushButton("Run finite first modeling")
    run_second = QPushButton("Run finite second correction")

    def run_first_clicked() -> None:
        if state.target_config is None:
            output.setPlainText("Target Config를 먼저 설정하십시오.")
            return
        result = run_finite_first_modeling(state.target_config, state.selected_finite_source or {})
        state.latest_finite_first_result = result
        output.setPlainText(_format_result("finite first modeling", result.status, result.error_reason))

    def run_second_clicked() -> None:
        if state.target_config is None or state.latest_finite_first_result is None:
            output.setPlainText("Target Config와 finite first result를 먼저 준비하십시오.")
            return
        result = run_finite_second_modeling(
            state.target_config,
            state.latest_finite_first_result,
            {"source_id": "not_selected"},
        )
        output.setPlainText(_format_result("finite second modeling", result.status, result.error_reason))

    run_first.clicked.connect(run_first_clicked)
    run_second.clicked.connect(run_second_clicked)
    layout.addWidget(QLabel("Finite production cycles: 1.0 / 1.5. Heavy calculation is button-based."))
    layout.addWidget(run_first)
    layout.addWidget(run_second)
    layout.addWidget(QLabel("Command plot placeholder"))
    layout.addWidget(output)
    return widget


def _format_result(label: str, status: str, error_reason: str | None) -> str:
    return f"{label}: status={status}\nerror_reason={error_reason or 'none'}"
