from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from coil_win_app.core_adapter import (
    ModelingResult,
    TargetConfig,
    finite_first_optional_metadata_keys,
    finite_first_required_metadata_keys,
    run_finite_first_modeling,
    run_finite_second_modeling,
)
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
        output.setPlainText(
            "\n".join(
                [
                    _format_config_summary(state.target_config),
                    _format_source_summary("Selected finite source", state.selected_finite_source),
                    _format_source_summary("Selected actual-drive source", state.selected_actual_drive_source),
                    _format_result("finite first modeling", result),
                ]
            )
        )

    def run_second_clicked() -> None:
        if state.target_config is None or state.latest_finite_first_result is None:
            output.setPlainText("Target Config와 finite first result를 먼저 준비하십시오.")
            return
        result = run_finite_second_modeling(
            state.target_config,
            state.latest_finite_first_result,
            state.selected_actual_drive_source or {},
        )
        output.setPlainText(
            "\n".join(
                [
                    _format_config_summary(state.target_config),
                    _format_source_summary("Selected finite source", state.selected_finite_source),
                    _format_source_summary("Selected actual-drive source", state.selected_actual_drive_source),
                    _format_result("finite second modeling", result),
                ]
            )
        )

    run_first.clicked.connect(run_first_clicked)
    run_second.clicked.connect(run_second_clicked)
    layout.addWidget(QLabel("Finite production cycles: 1.0 / 1.5. Heavy calculation is button-based."))
    layout.addWidget(QLabel("Selected finite source and actual-drive source are read from Project / Data."))
    layout.addWidget(run_first)
    layout.addWidget(run_second)
    layout.addWidget(QLabel("Command plot placeholder"))
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
    lines = [
        f"{label}: status={result.status}",
        f"error_reason={result.error_reason or 'none'}",
        f"source filename={result.metadata.get('selected_source_filename', 'not selected')}",
        f"required_core_api={result.metadata.get('required_core_api', 'none')}",
    ]
    if result.status == "missing_source":
        lines.append("Project/Data에서 finite source를 먼저 선택하십시오.")
    elif result.status == "schema_unavailable":
        lines.append("missing column groups=" + ", ".join(result.metadata.get("missing_column_groups", [])))
    elif result.status == "not_connected":
        lines.append("core API 연결 대기 상태입니다.")
    elif result.status == "ok" and result.command_profile is not None:
        lines.append(f"command_profile rows={len(result.command_profile)}")
        lines.append("voltage source=limited_voltage_v")
        lines.extend(_format_finite_first_metadata(result))
    return "\n".join(lines)


def _format_finite_first_metadata(result: ModelingResult) -> list[str]:
    lines = ["finite first compatibility metadata:"]
    for key in finite_first_required_metadata_keys() + finite_first_optional_metadata_keys() + ["clipping_fraction"]:
        lines.append(f"{key}={result.metadata.get(key, 'not available')}")
    return lines
