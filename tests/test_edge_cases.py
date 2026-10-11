"""Unit tests for complex edge cases: unusual amounts, leap year dates, noise strings."""

import pytest
from src.normalization import normalize_amount, normalize_date, validate_gstin


def test_amount_with_heavy_formatting():
    assert normalize_amount("Total Amount : INR 1,45,200.50 /-") == 145200.50
    assert normalize_amount("Rs.0.50") == 0.50
    assert normalize_amount("FREE") is None


def test_leap_year_date():
    iso, err = normalize_date("29/02/2024")
    assert iso == "2024-02-29"
    assert err is None


def test_gstin_edge_cases():
    # Valid Delhi GSTIN (07)
    valid_delhi = "07AAAAA0000A1Z5"
    ok, _ = validate_gstin(valid_delhi)
    assert ok is True

    # 14 chars (too short)
    ok, _ = validate_gstin("07AAAAA0000A1Z")
    assert ok is False
