"""Quarterly period parsing and validation helpers."""

from __future__ import annotations

import re


PERIOD_RE = re.compile(r"^(\d{4})Q([1-4])$")


def period_to_int(period: str) -> int:
    """Convert ``YYYYQ#`` to a monotone quarter integer."""
    match = PERIOD_RE.match(str(period))
    if not match:
        raise ValueError(f"Invalid quarterly period: {period!r}")
    year = int(match.group(1))
    quarter = int(match.group(2))
    return year * 4 + quarter - 1


def int_to_period(value: int) -> str:
    """Convert a monotone quarter integer back to ``YYYYQ#``."""
    year, q0 = divmod(int(value), 4)
    return f"{year}Q{q0 + 1}"


def quarter_range(start: str, end: str) -> list[str]:
    """Return inclusive quarterly labels from start through end."""
    a = period_to_int(start)
    b = period_to_int(end)
    if b < a:
        raise ValueError(f"End period {end!r} precedes start period {start!r}")
    return [int_to_period(i) for i in range(a, b + 1)]


def enforce_quarterly_continuity(periods: list[str], start: str | None = None, end: str | None = None) -> None:
    """Raise when periods are not sorted, unique, and contiguous."""
    if not periods:
        raise ValueError("No periods supplied")
    ints = [period_to_int(p) for p in periods]
    expected = list(range(ints[0], ints[0] + len(ints)))
    if ints != expected:
        raise ValueError("Periods must be sorted, unique, and quarterly-contiguous")
    if start is not None and periods[0] != start:
        raise ValueError(f"Expected start {start}, found {periods[0]}")
    if end is not None and periods[-1] != end:
        raise ValueError(f"Expected end {end}, found {periods[-1]}")

