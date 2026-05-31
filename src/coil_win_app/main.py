from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coil_win_app.core_adapter import get_core_version


def main() -> int:
    if "--smoke" in sys.argv:
        print(f"WinApp smoke ok: {get_core_version()}")
        return 0
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("PySide6 is not installed. Install project dependencies to launch the Windows UI.")
        print(f"Core adapter: {get_core_version()}")
        return 0

    from coil_win_app.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
