# Reproducibility

## Python

Target Python version: 3.11.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Conda:

```bash
conda env create -f environment.yml
conda activate dynamic-limits-growth-ukf
```

## Commands

Smoke test:

```bash
python scripts/run_smoke_test.py
```

Baseline smoke:

```bash
python scripts/run_pipeline.py --config configs/baseline.yaml --smoke
```

Full run:

```bash
python scripts/run_pipeline.py --config configs/baseline.yaml
```

`FREEZE_REFRESH_MODE` defaults to false. Refreshing freeze-style artifacts requires explicit opt-in through CLI/config rather than silent updates.

Each run writes `run_manifest.json` with commit, input hashes, package versions, outputs, warnings, and stability status.

