from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectState:
    project_path: Path | None = None
    data_path: Path | None = None

    def set_project_path(self, value: str | Path) -> None:
        self.project_path = Path(value).expanduser()

    def set_data_path(self, value: str | Path) -> None:
        self.data_path = Path(value).expanduser()
