from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QWidget

from coil_win_app.core_adapter import build_target_config


def create_target_config_page() -> QWidget:
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
        preview.setPlainText(str(config))

    build_button = QPushButton("Build TargetConfig Preview")
    build_button.clicked.connect(update_preview)
    layout.addRow("mode", mode_box)
    layout.addRow("freq_hz", freq_input)
    layout.addRow("finite cycle", cycle_box)
    layout.addRow("target shape", QLabel("fixed_rounded_triangle (read-only)"))
    layout.addRow("target peak field mT", peak_input)
    layout.addRow("voltage limit", QLabel("±10V (read-only policy)"))
    layout.addRow("source waveform family", family_input)
    layout.addRow(build_button)
    layout.addRow(preview)
    return widget
