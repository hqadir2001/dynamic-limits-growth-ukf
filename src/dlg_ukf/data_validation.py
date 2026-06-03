"""Canonical panel validation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .identity_anchors import resolve_observable_aliases
from .periods import enforce_quarterly_continuity


PB_IDENTITY_COLUMNS = ["FGRECPT", "FGEXPND", "A091RC1Q027SBEA", "GDP", "PB", "PB_GDP"]


@dataclass(frozen=True)
class PanelValidation:
    rows: int
    start: str
    end: str
    alias_map: dict[str, str]
    warnings: list[str]


def validate_pb_identity(df: pd.DataFrame, atol_pb: float = 1.0e-6, atol_ratio: float = 1.0e-8) -> None:
    missing = [col for col in PB_IDENTITY_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing PB identity columns: {missing}")
    calc_pb = df["FGRECPT"] - df["FGEXPND"] + df["A091RC1Q027SBEA"]
    calc_ratio = calc_pb / df["GDP"]
    if not np.allclose(df["PB"], calc_pb, atol=atol_pb, rtol=0.0, equal_nan=False):
        raise ValueError("PB identity failed: PB != FGRECPT - FGEXPND + A091RC1Q027SBEA")
    if not np.allclose(df["PB_GDP"], calc_ratio, atol=atol_ratio, rtol=0.0, equal_nan=False):
        raise ValueError("PB_GDP identity failed: PB_GDP != PB / GDP")


def panel_window(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    if "period" not in df.columns:
        raise ValueError("Panel must include period column")
    periods = df["period"].astype(str).tolist()
    enforce_quarterly_continuity(periods)
    subset = df[(df["period"].astype(str) >= start) & (df["period"].astype(str) <= end)].copy()
    enforce_quarterly_continuity(subset["period"].astype(str).tolist(), start, end)
    return subset


def validate_required_observables(df: pd.DataFrame, required: list[str]) -> dict[str, str]:
    alias_map = resolve_observable_aliases(required, df.columns.tolist())
    bad: list[str] = []
    for logical, physical in alias_map.items():
        values = pd.to_numeric(df[physical], errors="coerce")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            bad.append(f"{logical}->{physical}")
    if bad:
        raise ValueError(f"Required observables contain non-finite values: {bad}")
    return alias_map


def validate_canonical_panel(
    df: pd.DataFrame,
    *,
    start: str,
    end: str,
    required_observables: list[str],
    strict_rows: bool = True,
) -> PanelValidation:
    windowed = panel_window(df, start, end)
    expected_rows = 87
    warnings: list[str] = []
    if strict_rows and len(windowed) != expected_rows:
        raise ValueError(f"Expected {expected_rows} quarterly rows, found {len(windowed)}")
    if not strict_rows and len(windowed) != expected_rows:
        warnings.append(f"Non-canonical row count used for smoke/sample run: {len(windowed)}")
    validate_pb_identity(windowed)
    alias_map = validate_required_observables(windowed, required_observables)
    return PanelValidation(
        rows=len(windowed),
        start=str(windowed["period"].iloc[0]),
        end=str(windowed["period"].iloc[-1]),
        alias_map=alias_map,
        warnings=warnings,
    )

