# Dynamic Limits of Growth UKF

[![tests](https://github.com/hqadir2001/dynamic-limits-growth-ukf/actions/workflows/tests.yml/badge.svg)](https://github.com/hqadir2001/dynamic-limits-growth-ukf/actions/workflows/tests.yml)

System-dynamics-informed macro-financial stress analysis using a nonlinear state-space model estimated with an Unscented Kalman Filter on post-2003 U.S. data.

## Abstract

This repository contains a reproducible research-code package for a senior project on financial crises, structural imbalances, behavioural complacency, institutional rigidity, and policy cost-deferral. The empirical object is a locked quarterly U.S. macro-financial panel covering 2003Q4-2025Q2. The model is calibrated/semi-structural: it filters and smooths latent state paths conditional on the specified model, observables, and noise assumptions.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_smoke_test.py
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts\run_smoke_test.py
```

## Installation

Target Python version: 3.11.

Pip:

```bash
pip install -r requirements.txt
```

Conda:

```bash
conda env create -f environment.yml
conda activate dynamic-limits-growth-ukf
```

## Run Commands

Smoke pipeline:

```bash
python scripts/run_pipeline.py --config configs/baseline.yaml --smoke
```

Full baseline pipeline:

```bash
python scripts/run_pipeline.py --config configs/baseline.yaml
```

Optional flags:

```text
--project-root
--data-path
--results-dir
--refresh-freeze
--run-robustness
--run-counterfactuals
```

`FREEZE_REFRESH_MODE` defaults to false. Refreshing freeze-style artifacts requires explicit CLI/config opt-in.

## Expected Outputs

| output | description |
|---|---|
| `filtered_states_<tag>.csv` | Forward UKF state estimates |
| `smoothed_states_<tag>.csv` | RTS-style backward-pass state estimates |
| `state_covariance_diag_<tag>.csv` | Smoothed covariance diagonal |
| `fitted_values_<tag>.csv` | Measurement values implied by filtered states |
| `residuals_<tag>.csv` | Observed minus fitted values |
| `residual_summary_<tag>.csv` | Residual mean, dispersion, RMSE, and max absolute residual |
| `stability_report_<tag>.json` | Finiteness, likelihood, PSD repair, and smoother metadata |
| `run_manifest.json` | Commit, input hashes, config hash, package versions, output paths, warnings |

Generated outputs are written under `results/` and are excluded from Git by default.

## Repository Structure

```text
src/dlg_ukf/              Modular package code
scripts/                  CLI entry points
configs/                  Human-readable YAML configs
tests/                    Pytest coverage
data/processed/           Committed canonical processed panel
data/sample/              Small sample panel for smoke checks
docs/                     Model, reproducibility, limitations, outputs, counterfactuals
notebooks/                Clean reproduction notebook
notebooks/legacy/         Preserved original research notebook
```

## Implementation Scope

The repository now contains both:

1. a preserved legacy notebook under `notebooks/legacy/`, and
2. a modular Python package under `src/dlg_ukf/`.

The modular package is cleaner, testable, and suitable for smoke runs and software review. It should not yet be represented as a numerically identical port of the full legacy notebook. A future parity pass should compare modular outputs against the legacy notebook before using the modular package as the sole authoritative research pipeline.

## Data Note

The repository preserves the processed canonical panel and sample panel. Raw/private/intermediate data are intentionally excluded. The data dictionary is scaffolded and uses `TODO_VERIFY` for unknown source, unit, description, and transformation metadata rather than fabricating provenance.

## Limitations

This is research code, not a production forecasting system. UKF filtering is not causal identification. Counterfactuals are fixed-shock within-model comparisons, not causal policy effects. Historical decomposition is model-accounting attribution, not external causal attribution. Results depend on data construction, observables, model specification, and noise assumptions.

## Citation

See `CITATION.cff`.

## License

Code is released under the MIT License. Paper text, figures, and data-source materials may be subject to separate source or institutional restrictions.
