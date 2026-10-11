"""Automated tests for dataset loading, schema validation, and image mapping."""

from pathlib import Path
import pytest
import pandas as pd

from src.data import (
    ImageResolver,
    ImageResolutionStatus,
    load_claims_test,
    load_claims_train,
    load_employees,
    load_sample_submission,
)


def test_load_claims_train():
    df = load_claims_train()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 283
    expected_cols = [
        "claim_id", "emp_id", "submitted_on", "expense_date", "category",
        "vendor", "amount_claimed", "image_file", "status"
    ]
    for col in expected_cols:
        assert col in df.columns


def test_load_claims_test():
    df = load_claims_test()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 190
    expected_cols = [
        "claim_id", "emp_id", "submitted_on", "expense_date", "category",
        "vendor", "amount_claimed", "image_file"
    ]
    for col in expected_cols:
        assert col in df.columns


def test_load_employees():
    df = load_employees()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 16
    assert "emp_id" in df.columns
    assert "grade" in df.columns
    assert "vehicle_no" in df.columns


def test_load_sample_submission():
    df = load_sample_submission()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 190
    expected_cols = [
        "claim_id", "vendor", "receipt_date", "receipt_number",
        "gstin", "total_amount", "decision", "reason"
    ]
    assert list(df.columns) == expected_cols


def test_image_resolver():
    resolver = ImageResolver()
    # Test resolving known exact image
    path, status, msg = resolver.resolve("IMG_20260718_111930.jpg")
    assert status == ImageResolutionStatus.RESOLVED
    assert path is not None
    assert path.exists()

    # Test mobile full path
    mobile_path = "/storage/emulated/0/DCIM/Camera/IMG_20260718_111930.jpg"
    path, status, msg = resolver.resolve(mobile_path)
    assert status == ImageResolutionStatus.RESOLVED
    assert path is not None

    # Test missing upload reference
    path, status, msg = resolver.resolve(None)
    assert status == ImageResolutionStatus.MISSING_UPLOAD
    assert path is None

    # Test non-existent file
    path, status, msg = resolver.resolve("NON_EXISTENT_RECEIPT_9999.jpg")
    assert status == ImageResolutionStatus.NOT_FOUND
    assert path is None
