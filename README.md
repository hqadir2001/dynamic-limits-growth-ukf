# Dynamic Limits of Growth UKF

System-dynamics-informed macro-financial stress analysis using a nonlinear state-space model estimated with an Unscented Kalman Filter on post-2003 U.S. data.

## Overview

This repository contains the research-code package for a senior project on financial crises, structural imbalances, behavioural complacency, institutional rigidity, and policy cost-deferral. The project develops a Dynamic Limits of Growth framework and operationalizes it through a semi-structural nonlinear state-space model estimated with an Unscented Kalman Filter.

The empirical object is a locked quarterly U.S. macro-financial panel covering 2003Q4–2025Q2. The model uses 14 observable series, including output, output gap, inflation, unemployment, interest-rate and spread measures, financial-stress measures, public-debt and primary-balance anchors, external-balance anchors, net-foreign-asset anchors, and central-bank balance-sheet measures.

## Motivation

Financial crises are often treated as exogenous shocks or isolated policy failures. This project instead studies how crises can emerge endogenously when a growth regime accumulates structural imbalances, normalizes leverage and risk-taking, and develops institutions that defer rather than realize losses. The goal is to provide an auditable computational framework for tracing those dynamics in post-2003 U.S. macro-financial data.

## Methodology

The workflow is:

1. Load and validate the canonical quarterly data panel.
2. Enforce period integrity, observable completeness, and identity-anchor discipline.
3. Lock the measurement object and record hashes/provenance.
4. Estimate/filter latent states using a nonlinear state-space model and Unscented Kalman Filter.
5. Produce diagnostics, residual checks, smoothed/filtered states, historical-decomposition outputs, counterfactual policy-path outputs, and robustness artifacts.

Counterfactuals are fixed-shock, within-model scenario comparisons. They should not be interpreted as causal policy effects. Historical decomposition is accounting attribution inside the fitted system, not external causal identification.

## Repository structure

```text
.
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── GITHUB_UPLOAD_PLAN.md
├── PROJECT_MANIFEST.csv
├── data/
│   ├── README.md
│   ├── processed/master_panel_canonical.csv
│   └── sample/master_panel_sample.csv
├── docs/
│   ├── figures/dlg_stock_flow_map.pdf
│   └── paper/senior_project_writeup.pdf
├── notebooks/
│   └── 01_research_pipeline.ipynb
└── results/
    └── README.md
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Set the project root and run the notebook:

```bash
export SPROJ_ROOT=/path/to/dynamic-limits-growth-ukf
jupyter lab notebooks/01_research_pipeline.ipynb
```

On Windows PowerShell:

```powershell
$env:SPROJ_ROOT = "C:\path\to\dynamic-limits-growth-ukf"
jupyter lab notebooks/01_research_pipeline.ipynb
```

The notebook expects the canonical processed panel at:

```text
data/processed/master_panel_canonical.csv
```

Generated model outputs are written under:

```text
results/
```

Generated outputs are excluded from Git by default. Commit only selected publication-facing figures or compact summary tables.

## Data

The repository includes a cleaned processed panel and a small sample panel for inspection or smoke testing. Raw data downloads and large intermediate source files are not committed by default. The underlying series are public macro-financial data from sources such as FRED, BEA, BLS, IMF, and related official/public datasets. See `data/README.md` for details, caveats, required observables, identity anchors, and redistribution notes.

## Key outputs

The pipeline can produce:

- locked evaluation panel
- canonical specs and provenance files
- filtered and smoothed state estimates
- fitted values and residuals
- innovation diagnostics
- measurement-consistency residuals
- historical decomposition tables
- fixed-shock counterfactual scenario paths
- robustness summaries
- paper-facing figures and tables

Generated outputs are intentionally excluded from Git by default. Promote only selected publication-facing figures or compact tables when needed.

## Limitations and interpretation warning

This is a research-code repository, not a production forecasting package. The model is semi-structural and model-conditional. It does not provide causal identification, policy-invariant structural parameters, or proof that any historical crisis was inevitable. Results depend on the locked data object, selected observables, model specification, UKF assumptions, and fixed-shock counterfactual discipline.

## Author

Husnain Qadir

## License

Code is released under the MIT License. Paper text, figures, and data-source materials may be subject to separate source or institutional restrictions.
