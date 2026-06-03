import pytest

from dlg_ukf.periods import enforce_quarterly_continuity, period_to_int, quarter_range


def test_period_to_int():
    assert period_to_int("2003Q4") == 2003 * 4 + 3
    assert period_to_int("2025Q2") == 2025 * 4 + 1
    with pytest.raises(ValueError):
        period_to_int("2025Q5")
    with pytest.raises(ValueError):
        period_to_int("bad")


def test_continuity_checks():
    periods = quarter_range("2003Q4", "2004Q2")
    enforce_quarterly_continuity(periods, "2003Q4", "2004Q2")
    with pytest.raises(ValueError):
        enforce_quarterly_continuity(["2003Q4", "2004Q2"])

