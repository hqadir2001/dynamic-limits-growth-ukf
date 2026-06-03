"""Fixed-shock counterfactual helpers."""

from __future__ import annotations

from typing import Any

from .periods import period_to_int


WARNING = "Fixed-shock within-model comparison; not a causal policy effect."


def parse_window(start: str, end: str) -> tuple[str, str]:
    if period_to_int(end) < period_to_int(start):
        raise ValueError(f"Invalid counterfactual window: {start} to {end}")
    return start, end


def scenario_manifest(config: dict[str, Any], *, baseline_tag: str, input_hashes: dict[str, str], created_utc: str) -> dict[str, Any]:
    cf = config.get("counterfactuals", {})
    window = cf.get("window", {"start": "2020Q2", "end": "2021Q4"})
    start, end = parse_window(window["start"], window["end"])
    return {
        "baseline_tag": baseline_tag,
        "scenario_id": cf.get("scenario_id", "lambda_grid"),
        "lambda_grid": cf.get("lambda_grid", [1.0, 0.75, 0.5, 0.0]),
        "window": {"start": start, "end": end},
        "input_hashes": input_hashes,
        "generated_utc": created_utc,
        "warning": WARNING,
    }

