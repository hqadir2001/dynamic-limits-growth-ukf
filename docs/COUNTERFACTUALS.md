# Counterfactuals

Counterfactual settings live in `configs/counterfactuals.yaml`.

The default window is 2020Q2 to 2021Q4. Lambda values scale scenario intensity on a fixed-shock path:

```text
[1.0, 0.75, 0.5, 0.0]
```

These are fixed-shock within-model comparisons. They are not causal policy effects. Scenario manifests include the baseline tag, scenario id, lambda grid, window, input hashes, generated UTC time, and the non-causal warning.

