from __future__ import annotations

import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent / "src"
if SRC_DIR.exists():
    src_text = str(SRC_DIR)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)
