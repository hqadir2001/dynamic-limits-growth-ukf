# Model

The Dynamic Limits of Growth UKF model is a calibrated/semi-structural nonlinear state-space model for post-2003 U.S. macro-financial stress analysis. It is filtering and smoothing latent state paths conditional on a chosen model and data construction; it is not full structural parameter estimation.

## State Vector

| index | state |
|---:|---|
| 0 | logY |
| 1 | y_gap |
| 2 | pi |
| 3 | U |
| 4 | rS |
| 5 | term |
| 6 | hy_oas |
| 7 | nfci |
| 8 | vix |
| 9 | debt |
| 10 | pb |
| 11 | nx |
| 12 | nfa |
| 13 | cb_assets |
| 14 | growth_limit |
| 15 | fragility |
| 16 | policy_rigidity |
| 17 | complacency |

## Observables

The baseline observable vector uses output, output gap, inflation, unemployment, short-rate, term-spread, high-yield spread, financial-condition, volatility, public-debt, primary-balance, net-export, NFA, and central-bank-asset anchors. Identity anchors bind to raw columns `D_G_Y`, `PB_GDP`, `NX_Y`, `NFA_to_Y`, and `cb_assets_Y`.

## Equations

Transition equations are semi-structural calibrated recursions with persistence, stress feedback, debt/primary-balance interaction, and balance-sheet feedback. Measurement equations map the first fourteen states to the observable vector. Measurement consistency residuals are observed minus fitted values.

## Parameters

Parameters live in `ModelParams` and config noise settings. They are calibrated defaults, not estimated structural primitives.

## UKF And Smoother

The UKF propagates sigma points through the nonlinear transition and updates against available observations. The smoother is an additive-noise UKF/RTS backward pass using stored predicted covariances and filtered-to-predicted cross-covariances.

## Implementation Scope And Legacy-Parity Status

The modular `src/dlg_ukf/` package is an auditable, testable implementation scaffold for the project. It is not yet certified as numerically equivalent to the preserved legacy notebook under `notebooks/legacy/01_research_pipeline_legacy.ipynb`.

The legacy notebook remains the archival full research pipeline. Before treating the modular package as the definitive replacement, a future parity pass should port the full legacy transition equations, staged update logic, diagnostics, historical decomposition, and counterfactual machinery into `src/dlg_ukf/`, then compare key outputs against legacy outputs.

Current modular limitations:

- The modular package uses a simplified 18-state semi-structural model.
- Stage A / Stage B update logic from the legacy notebook is not yet fully restored.
- The smoother is real and uses a backward UKF/RTS-style pass, but model-equation parity with the legacy notebook is not yet established.
- Published empirical claims should continue to reference the legacy notebook or archived outputs until parity is verified.
