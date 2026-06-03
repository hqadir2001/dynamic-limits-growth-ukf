"""Run the modular Dynamic Limits of Growth UKF pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dlg_ukf.config import load_config
from dlg_ukf.counterfactuals import scenario_manifest
from dlg_ukf.data_validation import panel_window, validate_canonical_panel
from dlg_ukf.diagnostics import (
    covariance_diag_frame,
    nis_summary,
    observable_frame,
    outlier_quarters,
    output_integrity_check,
    residual_acf,
    residual_summary,
    stability_report,
    states_frame,
)
from dlg_ukf.historical_decomposition import build_historical_decomposition
from dlg_ukf.io_utils import build_run_manifest, sha256_file, utc_now, write_csv, write_json
from dlg_ukf.model_spec import compile_model_spec
from dlg_ukf.paths import infer_project_root, resolve_data_path, resolve_results_dir
from dlg_ukf.plotting import plot_fit
from dlg_ukf.smoother import rts_smoother
from dlg_ukf.ukf import run_filter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline.yaml")
    parser.add_argument("--project-root")
    parser.add_argument("--data-path")
    parser.add_argument("--results-dir")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--refresh-freeze", action="store_true")
    parser.add_argument("--run-robustness", action="store_true")
    parser.add_argument("--run-counterfactuals", action="store_true")
    return parser.parse_args()


def run_pipeline(args: argparse.Namespace) -> dict[str, str]:
    project_root = infer_project_root(args.project_root)
    config_path = (project_root / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config)
    config = load_config(config_path, {"refresh_freeze_confirmed": bool(args.refresh_freeze)})
    data_path = resolve_data_path(project_root, args.data_path)
    results_root = resolve_results_dir(project_root, args.results_dir)
    run_tag = str(config.get("outputs", {}).get("run_tag", "baseline"))
    if args.smoke:
        run_tag = f"{run_tag}_smoke"
    run_dir = results_root / run_tag
    run_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    window = config["evaluation_window"]
    validate_start = window["start"]
    validate_end = window["end"]
    if args.smoke and (str(df["period"].iloc[0]) != validate_start or str(df["period"].iloc[-1]) != validate_end):
        validate_start = str(df["period"].iloc[0])
        validate_end = str(df["period"].iloc[-1])
    validation = validate_canonical_panel(
        df,
        start=validate_start,
        end=validate_end,
        required_observables=config["required_observables"],
        strict_rows=not args.smoke,
    )
    panel = panel_window(df, validate_start, validate_end)
    if args.smoke:
        panel = panel.head(5).copy()
    spec = compile_model_spec(panel, config)
    result = run_filter(panel, spec, config)
    smooth = rts_smoother(result, float(config.get("ukf", {}).get("psd_epsilon", 1.0e-9)))

    filtered = states_frame(result.periods, spec.state_names, result.filtered_means)
    smoothed = states_frame(result.periods, spec.state_names, smooth.smoothed_means)
    cov_diag = covariance_diag_frame(result.periods, spec.state_names, smooth.smoothed_covariances)
    fitted = observable_frame(result.periods, spec.obs_logical, result.fitted_values)
    residuals = observable_frame(result.periods, spec.obs_logical, result.residuals)
    res_summary = residual_summary(residuals, spec.obs_logical)
    stability = stability_report(result, smooth)
    warnings = list(validation.warnings) + output_integrity_check(
        {"filtered_states": filtered, "smoothed_states": smoothed, "fitted_values": fitted, "residuals": residuals}
    )
    outputs = {
        "filtered_states": str(write_csv(run_dir / f"filtered_states_{run_tag}.csv", filtered)),
        "smoothed_states": str(write_csv(run_dir / f"smoothed_states_{run_tag}.csv", smoothed)),
        "state_covariance_diag": str(write_csv(run_dir / f"state_covariance_diag_{run_tag}.csv", cov_diag)),
        "fitted_values": str(write_csv(run_dir / f"fitted_values_{run_tag}.csv", fitted)),
        "residuals": str(write_csv(run_dir / f"residuals_{run_tag}.csv", residuals)),
        "residual_summary": str(write_csv(run_dir / f"residual_summary_{run_tag}.csv", res_summary)),
        "residual_acf": str(write_csv(run_dir / f"residual_acf_{run_tag}.csv", residual_acf(residuals, spec.obs_logical))),
        "outlier_quarters": str(write_csv(run_dir / f"outlier_quarters_{run_tag}.csv", outlier_quarters(residuals, spec.obs_logical))),
        "nis_summary": str(write_csv(run_dir / f"nis_summary_{run_tag}.csv", nis_summary(result))),
    }
    decomp, decomp_report = build_historical_decomposition(result.periods, fitted)
    outputs["historical_decomposition"] = str(write_csv(run_dir / f"historical_decomposition_{run_tag}.csv", decomp))
    outputs["historical_decomposition_report"] = str(write_json(run_dir / f"historical_decomposition_report_{run_tag}.json", decomp_report))
    outputs["stability_report"] = str(write_json(run_dir / f"stability_report_{run_tag}.json", stability))
    outputs["smoother_metadata"] = str(write_json(run_dir / f"smoother_metadata_{run_tag}.json", smooth.metadata))
    plot_paths = plot_fit(fitted, residuals, run_dir / "figures", run_tag)
    if plot_paths:
        outputs["fit_plots"] = str(run_dir / "figures")
    if args.run_counterfactuals:
        manifest = scenario_manifest(
            config,
            baseline_tag=run_tag,
            input_hashes={"panel": sha256_file(data_path), "config": sha256_file(config_path)},
            created_utc=utc_now(),
        )
        outputs["counterfactual_manifest"] = str(write_json(run_dir / f"counterfactual_manifest_{run_tag}.json", manifest))

    manifest = build_run_manifest(
        run_tag=run_tag,
        project_root=project_root,
        input_panel_path=data_path,
        config_path=config_path,
        outputs=outputs,
        warnings=warnings,
        stability_status=str(stability["status"]),
    )
    outputs["run_manifest"] = str(write_json(run_dir / "run_manifest.json", manifest))
    return outputs


def main() -> None:
    outputs = run_pipeline(parse_args())
    print(outputs["run_manifest"])


if __name__ == "__main__":
    main()
