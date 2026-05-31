from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget


def create_finite_modeling_page() -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    output = QTextEdit()
    output.setReadOnly(True)
    run_first = QPushButton("Run finite first modeling")
    run_second = QPushButton("Run finite second correction")
    run_first.clicked.connect(lambda: output.setPlainText("finite first modeling: core adapter not_connected"))
    run_second.clicked.connect(lambda: output.setPlainText("finite second modeling: core adapter not_connected"))
    layout.addWidget(QLabel("Finite production cycles: 1.0 / 1.5. Heavy calculation is button-based."))
    layout.addWidget(run_first)
    layout.addWidget(run_second)
    layout.addWidget(QLabel("Command plot placeholder"))
    layout.addWidget(output)
    return widget
