# Outputs

Pipeline outputs are written under `results/<run_tag>/`.

| output | meaning |
|---|---|
| filtered states | Forward UKF state estimates |
| smoothed states | RTS-style backward-pass state estimates |
| covariance diagnostics | Smoothed covariance diagonal by state |
| fitted values | Measurement values implied by filtered states |
| residuals | Observed minus fitted values |
| innovations/NIS | Update diagnostics and normalized innovation summary |
| residual summary | Mean, standard deviation, RMSE, maximum absolute residual |
| stability report | Finiteness, likelihood, PSD repair, smoother metadata |
| variance stability report | Covered by covariance and stability outputs |
| measurement consistency residuals | Observable-level residuals |
| fit plots | Matplotlib fit/residual plots |
| timing plots | Reserved for reporting extensions |
| counterfactual outputs | Scenario manifest when enabled |
| historical decomposition outputs | Reconciled model-accounting attribution scaffold |
| run manifest | Machine-readable provenance and output manifest |

