"""Run a minimal smoke pipeline and fail on missing key outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_pipeline import run_pipeline


def main() -> None:
    args = argparse.Namespace(
        config="configs/baseline.yaml",
        project_root=str(ROOT),
        data_path=str(ROOT / "data" / "sample" / "master_panel_sample.csv"),
        results_dir=str(ROOT / "results"),
        smoke=True,
        refresh_freeze=False,
        run_robustness=False,
        run_counterfactuals=True,
    )
    outputs = run_pipeline(args)
    required = ["filtered_states", "smoothed_states", "state_covariance_diag", "residual_summary", "run_manifest"]
    missing = [key for key in required if key not in outputs or not Path(outputs[key]).exists()]
    if missing:
        raise SystemExit(f"Smoke test missing outputs: {missing}")
    print(outputs["run_manifest"])


if __name__ == "__main__":
    main()

