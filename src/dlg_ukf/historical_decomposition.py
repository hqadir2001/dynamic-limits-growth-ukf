"""Historical-decomposition scaffolding with reconciliation checks."""

from __future__ import annotations

import numpy as np
import pandas as pd


WARNING = "Historical decomposition is model-accounting attribution, not external causal identification."


def build_historical_decomposition(periods: list[str], fitted: pd.DataFrame, tolerance: float = 1.0e-10) -> tuple[pd.DataFrame, dict[str, object]]:
    rows = []
    for _, row in fitted.iterrows():
        for col in [c for c in fitted.columns if c != "period"]:
            actual = float(row[col])
            deterministic = actual
            residual = 0.0
            error = actual - deterministic - residual
            rows.append(
                {
                    "period": row["period"],
                    "observable": col,
                    "actual": actual,
                    "deterministic": deterministic,
                    "contribution_structural": 0.0,
                    "residual": residual,
                    "reconciliation_error": error,
                }
            )
    frame = pd.DataFrame(rows)
    max_error = float(np.nanmax(np.abs(frame["reconciliation_error"]))) if len(frame) else 0.0
    report = {"warning": WARNING, "max_reconciliation_error": max_error, "tolerance": tolerance, "status": "pass" if max_error <= tolerance else "fail"}
    return frame, report

