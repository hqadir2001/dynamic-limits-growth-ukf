import pandas as pd

from dlg_ukf.identity_anchors import bind_identity_anchors


def test_identity_anchor_binding():
    cols = ["D_G_Y", "PB_GDP", "NX_Y", "NFA_to_Y", "cb_assets_Y"]
    binding = bind_identity_anchors(cols)
    assert binding["debt_obs__sc"] == "D_G_Y"
    assert binding["pb_obs__sc"] == "PB_GDP"
    assert binding["nxY_obs__sc"] == "NX_Y"
    assert binding["nfa_y_obs__sc"] == "NFA_to_Y"
    assert binding["cb_assets_obs__sc"] == "cb_assets_Y"

