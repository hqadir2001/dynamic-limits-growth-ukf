"""Logical observable to raw-anchor binding."""

from __future__ import annotations

from dataclasses import dataclass


IDENTITY_ANCHORS = {
    "debt_obs__sc": "D_G_Y",
    "pb_obs__sc": "PB_GDP",
    "nxY_obs__sc": "NX_Y",
    "nfa_y_obs__sc": "NFA_to_Y",
    "cb_assets_obs__sc": "cb_assets_Y",
}


@dataclass(frozen=True)
class AnchorBinding:
    logical: str
    physical: str
    required: bool = True


def bind_identity_anchors(columns: list[str]) -> dict[str, str]:
    """Bind logical identity observables to required physical raw anchors."""
    available = set(columns)
    missing = [physical for physical in IDENTITY_ANCHORS.values() if physical not in available]
    if missing:
        raise ValueError(f"Missing required identity anchor columns: {missing}")
    return dict(IDENTITY_ANCHORS)


def resolve_observable_aliases(logical_observables: list[str], columns: list[str]) -> dict[str, str]:
    """Resolve logical observables to physical columns, preferring raw identity anchors."""
    bindings = bind_identity_anchors(columns)
    available = set(columns)
    resolved: dict[str, str] = {}
    for logical in logical_observables:
        if logical in bindings:
            resolved[logical] = bindings[logical]
        elif logical in available:
            resolved[logical] = logical
        else:
            raise ValueError(f"Missing required observable column: {logical}")
    return resolved

