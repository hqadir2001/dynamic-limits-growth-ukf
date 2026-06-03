# Data README

## Files included

- `processed/master_panel_canonical.csv`: cleaned canonical quarterly panel used by the model.
- `sample/master_panel_sample.csv`: first 12 rows of the processed panel for quick inspection and smoke testing.

## Panel coverage

- Frequency: quarterly
- Window: 2003Q4 to 2025Q2
- Rows: 87
- Columns in public processed panel: 295

## Cleaning applied for public release

The public processed panel was derived from the uploaded canonical master panel. For GitHub clarity:

1. The model-facing observable columns were aligned to the authoritative raw identity anchors:
   - `debt_obs__sc = D_G_Y`
   - `pb_obs__sc = PB_GDP`
   - `nxY_obs__sc = NX_Y`
   - `nfa_y_obs__sc = NFA_to_Y`
   - `cb_assets_obs__sc = cb_assets_Y`
2. Fully empty placeholder columns were removed: REER_gap, eps_NX__nominal, foreign_rate.
3. The primary-balance identity validates as `PB = FGRECPT - FGEXPND + A091RC1Q027SBEA`, and `PB_GDP = PB / GDP`.

## Required model observables

The core model requires the following observable columns to be complete over the evaluation window:

```text
logY_obs__sc
y_gap_obs__sc
pi_obs__sc
U_obs__sc
rS_obs__sc
term_obs__sc
hy_oas_obs__sc
nfci_obs__sc
vix_obs__sc
debt_obs__sc
pb_obs__sc
nxY_obs__sc
nfa_y_obs__sc
cb_assets_obs__sc
```

## Authoritative identity anchors

The following raw anchors should be treated as authoritative for fiscal, external, and central-bank-balance-sheet discipline:

```text
D_G_Y
PB_GDP
NX_Y
NFA_to_Y
cb_assets_Y
```

## Source and redistribution note

The panel is assembled from public macro-financial sources such as FRED, BEA, BLS, IMF, and related official/public datasets. Before publishing a full raw-data dump, verify each source's redistribution terms. For a portfolio repository, it is safer to publish the cleaned processed panel plus source notes, and exclude raw bulk downloads and generated intermediates.

## Known caveats

The broader source panel contains optional and experimental columns with missingness. These are not all required by the core model. The README and code should clearly distinguish required observables from optional diagnostics and future-work variables.
