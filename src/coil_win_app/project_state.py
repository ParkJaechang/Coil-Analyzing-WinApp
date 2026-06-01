from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coil_win_app.core_adapter import ModelingResult, TargetConfig


@dataclass
class ProjectState:
    project_path: Path | None = None
    data_path: Path | None = None
    target_config: TargetConfig | None = None
    selected_finite_source: dict[str, Any] | None = None
    selected_continuous_source: dict[str, Any] | None = None
    latest_finite_first_result: ModelingResult | None = None
    latest_continuous_first_result: ModelingResult | None = None
    latest_export_result: ModelingResult | None = None
    status_messages: list[str] | None = None

    def set_project_path(self, value: str | Path) -> None:
        self.project_path = Path(value).expanduser()

    def set_data_path(self, value: str | Path) -> None:
        self.data_path = Path(value).expanduser()

    def set_target_config(self, value: TargetConfig) -> None:
        self.target_config = value
        self.add_status("TargetConfig saved")

    def add_status(self, message: str) -> None:
        if self.status_messages is None:
            self.status_messages = []
        self.status_messages.append(str(message))
