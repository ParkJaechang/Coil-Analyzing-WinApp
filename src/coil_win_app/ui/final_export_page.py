from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from coil_win_app.core_adapter import build_final_lut_export, create_demo_modeling_result
from coil_win_app.project_state import ProjectState
from coil_win_app.result_diagnostics import explain_final_lut_export_eligibility


def create_final_export_page(state: ProjectState) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    preview = QTextEdit()
    preview.setReadOnly(True)
    status = QLabel("No latest finite first modeling result. Use demo only if you need to verify export UI.")
    build_export = QPushButton("Build Final LUT Export Preview")
    demo_export = QPushButton("Create Demo Export Preview")

    def build_preview_from_latest() -> None:
        result = state.latest_finite_first_result
        if result is None:
            status.setText("export unavailable: no latest finite first modeling result")
            preview.setPlainText("No latest finite first modeling result. command_profile is missing.")
            return
        eligibility = explain_final_lut_export_eligibility(result)
        if not eligibility["eligible"]:
            status.setText(f"export unavailable: {eligibility['blocking_reason']}")
            preview.setPlainText(_format_export_eligibility(eligibility))
            return
        status.setText(f"latest finite first result status={result.status}")
        export = build_final_lut_export(result)
        state.latest_export_result = export
        _show_export(export, preview, status)

    def build_demo_preview() -> None:
        result = create_demo_modeling_result()
        result.metadata["demo_only"] = True  # demo_only=True
        export = build_final_lut_export(result, allow_demo=True)
        export.metadata["demo_only"] = True
        state.latest_export_result = export
        _show_export(export, preview, status)

    build_export.clicked.connect(build_preview_from_latest)
    demo_export.clicked.connect(build_demo_preview)
    preview.setPlainText("sample_index,time_s,voltage_v\n0,0.000,0.000\n1,0.001,0.000")
    layout.addWidget(QLabel("Final LUT export uses plotted final voltage samples, not Fourier resynthesis."))
    layout.addWidget(QLabel("CSV columns exactly: sample_index,time_s,voltage_v"))
    layout.addWidget(QLabel("Demo only / modeling result 아님"))
    layout.addWidget(status)
    layout.addWidget(build_export)
    layout.addWidget(demo_export)
    layout.addWidget(preview)
    return widget


def _show_export(export, preview: QTextEdit, status: QLabel) -> None:
    if export.status != "ok" or export.export_frame is None:
        status.setText(f"export status={export.status}; error={export.error_reason or 'unknown'}")
        preview.setPlainText(export.error_reason or "export failed")
        return
    columns = list(export.export_frame.columns)
    if columns != ["sample_index", "time_s", "voltage_v"]:
        status.setText(f"export status=failed; invalid columns={columns}")
        preview.setPlainText("invalid final LUT schema")
        return
    status.setText(f"export status=ok; rows={len(export.export_frame)}; demo_only={export.metadata.get('demo_only', False)}")
    preview.setPlainText(export.export_frame.to_csv(index=False))


def _format_export_eligibility(eligibility: dict[str, object]) -> str:
    return "\n".join(
        [
            "Final LUT export eligibility:",
            f"eligible={eligibility.get('eligible')}",
            f"blocking_reason={eligibility.get('blocking_reason') or 'none'}",
            f"required_columns={', '.join(str(item) for item in eligibility.get('required_columns', []))}",
            f"actual_columns={', '.join(str(item) for item in eligibility.get('actual_columns', [])) or 'none'}",
        ]
    )
