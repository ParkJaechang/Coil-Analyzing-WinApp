from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


def create_final_export_page() -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    preview = QTextEdit()
    preview.setReadOnly(True)
    preview.setPlainText("sample_index,time_s,voltage_v\n0,0.000,0.000\n1,0.001,0.000")
    layout.addWidget(QLabel("Final LUT export uses plotted final voltage samples, not Fourier resynthesis."))
    layout.addWidget(QLabel("CSV columns exactly: sample_index,time_s,voltage_v"))
    layout.addWidget(QLabel("Dummy preview until core adapter is connected:"))
    layout.addWidget(preview)
    return widget
