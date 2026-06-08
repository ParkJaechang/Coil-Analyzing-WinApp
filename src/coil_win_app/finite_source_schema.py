from __future__ import annotations

from typing import Any

import pandas as pd

from coil_win_app.core_adapter import FINITE_FIRST_COLUMN_CANDIDATES, prepare_finite_first_input_frame, validate_finite_first_input_frame


def build_finite_first_source_schema_report(frame: pd.DataFrame) -> dict[str, Any]:
    prepared, schema = prepare_finite_first_input_frame(frame)
    validation = validate_finite_first_input_frame(frame)
    resolved = schema.get("resolved_columns") or validation.get("resolved_columns", {})
    missing = schema.get("missing_column_groups") or validation.get("missing_column_groups", [])
    rejected_reason = schema.get("rejected_reason")
    return {
        "status": schema.get("status", validation.get("status")),
        "missing_column_groups": list(missing),
        "resolved_columns": dict(resolved),
        "required_column_candidates": FINITE_FIRST_COLUMN_CANDIDATES,
        "prepared_columns": list(schema.get("prepared_columns", [str(column) for column in frame.columns])),
        "rejected_reason": rejected_reason,
        "row_count": int(len(frame)),
        "numeric_finite_counts": _numeric_finite_counts(frame, resolved),
        "final_lut_input_rejected": rejected_reason == "final_lut_export_schema_is_not_finite_first_input",
        "prepared_frame_available": prepared is not None,
    }


def _numeric_finite_counts(frame: pd.DataFrame, resolved_columns: dict[str, str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for group, column in resolved_columns.items():
        if column not in frame.columns:
            counts[group] = 0
            continue
        numeric = pd.to_numeric(frame[column], errors="coerce")
        finite = numeric.notna() & (numeric != float("inf")) & (numeric != float("-inf"))
        counts[group] = int(finite.sum())
    return counts
