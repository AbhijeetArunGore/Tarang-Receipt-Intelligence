"""Unit tests for field normalization: amounts, dates, GSTINs, and string cleaners."""

import pytest

from src.normalization import (
    normalize_amount,
    normalize_date,
    validate_gstin,
    normalize_bill_number,
    normalize_vendor_name,
)


def test_normalize_amount():
    assert normalize_amount("Rs. 1,234.50") == 1234.50
    assert normalize_amount("Rs 500/-") == 500.00
    assert normalize_amount("₹ 3,539.00") == 3539.00
    assert normalize_amount("330.4") == 330.40
    assert normalize_amount("Rs. 30") == 30.00
    assert normalize_amount(250.0) == 250.00
    assert normalize_amount(None) is None
    assert normalize_amount("") is None


def test_normalize_date():
    iso, err = normalize_date("18-07-2026")
    assert iso == "2026-07-18"
    assert err is None

    iso, err = normalize_date("2026-06-09")
    assert iso == "2026-06-09"
    assert err is None

    iso, err = normalize_date("18/07/2026")
    assert iso == "2026-07-18"
    assert err is None

    iso, err = normalize_date("invalid-date")
    assert iso is None
    assert err is not None


def test_validate_gstin():
    # Valid Maharashtra GSTIN (state 27)
    valid_gstin = "27AAAAA0000A1Z5"
    is_valid, norm = validate_gstin(valid_gstin)
    assert is_valid is True
    assert norm == "27AAAAA0000A1Z5"

    # With spaces and lower case
    is_valid, norm = validate_gstin(" 27aaaaa0000a1z5 ")
    assert is_valid is True
    assert norm == "27AAAAA0000A1Z5"

    # Invalid: PAN length mismatch
    is_valid, norm = validate_gstin("27AAAA0000A1Z5")
    assert is_valid is False

    # Empty / None
    is_valid, norm = validate_gstin(None)
    assert is_valid is False
    assert norm is None


def test_normalize_bill_number():
    assert normalize_bill_number("Bill No: INV-4029") == "INV-4029"
    assert normalize_bill_number("Invoice # 001452") == "001452"
    assert normalize_bill_number("Receipt No. RCP/2026/88") == "RCP/2026/88"
    assert normalize_bill_number("None") is None
    assert normalize_bill_number(None) is None


def test_normalize_vendor_name():
    assert normalize_vendor_name("HOTEL SHUBHAM") == "Hotel Shubham"
    assert normalize_vendor_name("Welcome to IOCL Petrol Pump") == "IOCL Petrol Pump"
    assert normalize_vendor_name("  Shree Ganesh Restaurant  ") == "Shree Ganesh Restaurant"
    assert normalize_vendor_name(None) is None
