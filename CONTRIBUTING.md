# Contributing

This repository is research code. Changes should preserve the model interpretation and document any numerical behavior changes.

Run before committing:

```bash
pytest
python scripts/run_smoke_test.py
python scripts/run_pipeline.py --config configs/baseline.yaml --smoke
```

Do not commit raw data, credentials, generated run folders, or private documents.

