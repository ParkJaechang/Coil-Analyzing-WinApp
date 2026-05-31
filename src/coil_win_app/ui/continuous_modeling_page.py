from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget


def create_continuous_modeling_page() -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    output = QTextEdit()
    output.setReadOnly(True)
    run_extract = QPushButton("Run steady-state 1cycle extraction")
    run_first = QPushButton("Run continuous first modeling")
    run_second = QPushButton("Run continuous second correction")
    run_extract.clicked.connect(lambda: output.setPlainText("continuous extraction: core adapter not_connected"))
    run_first.clicked.connect(lambda: output.setPlainText("continuous first modeling: core adapter not_connected"))
    run_second.clicked.connect(lambda: output.setPlainText("continuous second modeling: core adapter not_connected"))
    layout.addWidget(QLabel("Continuous production: steady-state 1cycle repeated output only."))
    layout.addWidget(run_extract)
    layout.addWidget(run_first)
    layout.addWidget(run_second)
    layout.addWidget(output)
    return widget
