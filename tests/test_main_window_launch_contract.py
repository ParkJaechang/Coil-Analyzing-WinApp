from __future__ import annotations

import os

import pytest


def test_main_window_constructs_with_shared_state() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")

    from coil_win_app.ui.main_window import MainWindow

    app = widgets.QApplication.instance() or widgets.QApplication([])
    window = MainWindow()

    assert window.state is not None
    assert window.centralWidget().count() == 5
    assert window.centralWidget().tabText(1) == "Target Config"

    window.close()
    app.processEvents()
