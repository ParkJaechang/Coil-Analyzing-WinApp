from __future__ import annotations

from typing import Any

import pandas as pd
from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from coil_win_app.core_adapter import (
    ModelingResult,
    TargetConfig,
    finite_first_optional_metadata_keys,
    finite_first_required_metadata_keys,
    run_finite_first_modeling,
    run_finite_second_modeling,
)
from coil_win_app.core_dependency import get_core_dependency_status
from coil_win_app.project_state import ProjectState
from coil_win_app.result_diagnostics import explain_final_lut_export_eligibility, format_finite_first_summary
from coil_win_app.runtime_diagnostics import build_core_status_summary


def create_finite_modeling_page(state: ProjectState) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    output = QTextEdit()
    output.setReadOnly(True)
    preflight = QLabel(_format_preflight(state))
    run_first = QPushButton("Run finite first modeling")
    run_second = QPushButton("Run finite second correction")

    def refresh_preflight() -> None:
        preflight.setText(_format_preflight(state))

    def run_first_clicked() -> None:
        refresh_preflight()
        if state.target_config is None:
            output.setPlainText("Target Config를 먼저 설정하십시오.")
            return
        state.add_status("finite first run started")
        result = run_finite_first_modeling(state.target_config, state.selected_finite_source or {})
        state.latest_finite_first_result = result
        eligibility = explain_final_lut_export_eligibility(result)
        state.add_status(f"finite first run completed: {result.status}")
        output.setPlainText(
            "\n".join(
                [
                    _format_config_summary(state.target_config),
                    _format_source_summary("Selected finite source", state.selected_finite_source),
                    _format_source_summary("Selected actual-drive source", state.selected_actual_drive_source),
                    format_finite_first_summary(result),
                    _format_export_eligibility(eligibility),
                    _format_result("finite first modeling", result),
                ]
            )
        )

    def run_second_clicked() -> None:
        refresh_preflight()
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
    layout.addWidget(preflight)
    layout.addWidget(run_first)
    layout.addWidget(run_second)
    layout.addWidget(QLabel("Command plot placeholder"))
    layout.addWidget(output)
    return widget


def _format_preflight(state: ProjectState) -> str:
    core_summary = build_core_status_summary(get_core_dependency_status())
    config = "not configured" if state.target_config is None else _format_config_summary(state.target_config)
    return "\n".join(
        [
            f"core severity={core_summary['severity']} | {core_summary['headline']} | blocking={core_summary['blocking_reason'] or 'none'}",
            config,
            _format_source_summary("Selected finite source", state.selected_finite_source),
            _format_source_summary("Selected actual-drive source", state.selected_actual_drive_source),
        ]
    )


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
    return (
        f"{label}: filename={record.get('filename', 'unknown')} | "
        f"category={record.get('category', 'unknown')} | size={record.get('file_size_bytes', 'unknown')}"
    )


def _format_export_eligibility(eligibility: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"final export candidate: {'yes' if eligibility['eligible'] else 'no'}",
            f"blocking_reason={eligibility.get('blocking_reason') or 'none'}",
            f"required_columns={eligibility.get('required_columns')}",
            f"actual_columns={eligibility.get('actual_columns')}",
        ]
    )


def _format_result(label: str, result: ModelingResult) -> str:
    lines = [
        f"{label}: status={result.status}",
        f"error_reason={result.error_reason or 'none'}",
        f"source filename={result.metadata.get('selected_source_filename', 'not selected')}",
        f"required_core_api={result.metadata.get('required_core_api', 'none')}",
    ]
    finite_status = result.metadata.get("finite_first_modeling_status")
    if finite_status is not None and finite_status != "ok":
        lines.append(f"finite_first_modeling_status != ok: {finite_status}")
    if result.status == "missing_source":
        lines.append("Project/Data에서 finite source를 먼저 선택하십시오.")
    elif result.status == "schema_unavailable":
        lines.append("missing column groups=" + ", ".join(result.metadata.get("missing_column_groups", [])))
        lines.extend(_format_schema_candidates(result.metadata.get("required_column_candidates", {})))
    elif result.status == "not_connected":
        lines.append("core API 연결 대기 상태입니다.")
        lines.append(f"core import available={result.metadata.get('core_import_available', 'unknown')}")
        missing = result.metadata.get("missing_core_modules", [])
        lines.append("missing core modules=" + (", ".join(missing) if missing else "none"))
        lines.append(f"added sys.path={result.metadata.get('added_sys_path') or 'none'}")
    elif result.status == "failed":
        lines.append("core call failed or source read failed; see error_reason above.")
    elif result.status == "ok" and result.command_profile is not None:
        lines.append(f"command_profile rows={len(result.command_profile)}")
        lines.append("voltage source=limited_voltage_v")
        lines.append(f"limited_voltage_v peak={_limited_voltage_peak(result)}")
        lines.extend(_format_finite_first_metadata(result))
    return "\n".join(lines)


def _format_finite_first_metadata(result: ModelingResult) -> list[str]:
    lines = ["finite first compatibility metadata:"]
    for key in finite_first_required_metadata_keys() + finite_first_optional_metadata_keys() + ["clipping_fraction"]:
        lines.append(f"{key}={result.metadata.get(key, 'not available')}")
    return lines


def _format_schema_candidates(candidates: object) -> list[str]:
    if not isinstance(candidates, dict) or not candidates:
        return []
    lines = ["accepted column candidates:"]
    for group, names in candidates.items():
        if isinstance(names, list):
            lines.append(f"{group}: {', '.join(str(name) for name in names)}")
    return lines


def _limited_voltage_peak(result: ModelingResult) -> str:
    profile = result.command_profile
    if profile is None or "limited_voltage_v" not in profile.columns:
        return "not available"
    values = pd.to_numeric(profile["limited_voltage_v"], errors="coerce").abs().dropna()
    if values.empty:
        return "not available"
    return f"{float(values.max()):g}"
