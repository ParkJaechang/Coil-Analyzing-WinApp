from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QWidget

from coil_win_app.core_adapter import build_target_config
from coil_win_app.project_state import ProjectState


def create_target_config_page(state: ProjectState) -> QWidget:
    widget = QWidget()
    layout = QFormLayout(widget)
    mode_box = QComboBox()
    mode_box.addItems(["finite_startup_aware", "continuous_steady_state"])
    freq_input = QLineEdit("1.0")
    cycle_box = QComboBox()
    cycle_box.addItems(["1.0", "1.5"])
    peak_input = QLineEdit("50.0")
    family_input = QLineEdit("sine")
    preview = QTextEdit()
    preview.setReadOnly(True)
    summary = QLabel("Current config: not saved")

    def sync_cycle_policy() -> None:
        if mode_box.currentText() == "continuous_steady_state":
            cycle_box.setCurrentText("1.0")
            cycle_box.setEnabled(False)
            summary.setText("continuous mode locks cycle_count to 1.0")
        else:
            cycle_box.setEnabled(True)

    def update_preview() -> None:
        try:
            config = build_target_config(
                modeling_input_mode=mode_box.currentText(),
                freq_hz=float(freq_input.text()),
                cycle_count=float(cycle_box.currentText()),
                target_peak_field_mT=float(peak_input.text()),
                source_waveform_family=family_input.text(),
            )
        except Exception as exc:
            preview.setPlainText(f"TargetConfig error: {exc}")
            return
        state.set_target_config(config)
        summary.setText(
            "TargetConfig saved | mode={mode} | freq_hz={freq:g} | cycle_count={cycle:g} | "
            "target_peak_field_mT={peak:g} | target_shape={shape} | "
            "field_normalization_mode={norm} | voltage_limit_v={limit:g}".format(
                mode=config.modeling_input_mode,
                freq=config.freq_hz,
                cycle=config.cycle_count,
                peak=config.target_peak_field_mT,
                shape=config.target_shape,
                norm=config.field_normalization_mode,
                limit=config.voltage_limit_v,
            )
        )
        preview.setPlainText(f"TargetConfig saved\n{config}")

    build_button = QPushButton("Build TargetConfig Preview")
    build_button.clicked.connect(update_preview)
    mode_box.currentTextChanged.connect(lambda _value: sync_cycle_policy())
    layout.addRow("mode", mode_box)
    layout.addRow("freq_hz", freq_input)
    layout.addRow("finite cycle", cycle_box)
    layout.addRow("target shape", QLabel("fixed_rounded_triangle (read-only)"))
    layout.addRow("target peak field mT", peak_input)
    layout.addRow("voltage limit", QLabel("±10V (read-only policy)"))
    layout.addRow("source waveform family", family_input)
    layout.addRow(build_button)
    layout.addRow(summary)
    layout.addRow(preview)
    sync_cycle_policy()
    return widget
