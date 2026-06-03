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

