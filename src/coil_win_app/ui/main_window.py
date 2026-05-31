from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget

from coil_win_app.project_state import ProjectState
from coil_win_app.ui.continuous_modeling_page import create_continuous_modeling_page
from coil_win_app.ui.final_export_page import create_final_export_page
from coil_win_app.ui.finite_modeling_page import create_finite_modeling_page
from coil_win_app.ui.project_page import create_project_page
from coil_win_app.ui.target_config_page import create_target_config_page


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.state = ProjectState()
        self.setWindowTitle("Coil Analyzing Windows App")
        self.resize(1100, 760)

        tabs = QTabWidget()
        tabs.addTab(create_project_page(self.state), "Project / Data")
        tabs.addTab(create_target_config_page(), "Target Config")
        tabs.addTab(create_finite_modeling_page(), "Finite Modeling")
        tabs.addTab(create_continuous_modeling_page(), "Continuous Modeling")
        tabs.addTab(create_final_export_page(), "Final LUT Export")
        self.setCentralWidget(tabs)
