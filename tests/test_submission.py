"""Automated validation tests for predictions.csv submission artifact.

Ensures exact compliance with sample_submission.csv columns, row counts,
claim_id order, allowed decision vocabulary, and field formatting.
"""

import re
from pathlib import Path
import pytest
import pandas as pd

from src.config import PREDICTIONS_PATH, SAMPLE_SUBMISSION_PATH, CLAIMS_TEST_PATH


@pytest.fixture
def submission_df():
    if not PREDICTIONS_PATH.exists():
        pytest.skip("predictions.csv has not been generated yet.")
    return pd.read_csv(PREDICTIONS_PATH, dtype=str)


@pytest.fixture
def sample_submission_df():
    return pd.read_csv(SAMPLE_SUBMISSION_PATH, dtype=str)


@pytest.fixture
def test_claims_df():
    return pd.read_csv(CLAIMS_TEST_PATH, dtype=str)


def test_submission_file_exists():
    assert PREDICTIONS_PATH.exists(), f"predictions.csv missing at {PREDICTIONS_PATH}"


def test_submission_row_count(submission_df, test_claims_df):
    assert len(submission_df) == len(test_claims_df), (
        f"Row count mismatch: got {len(submission_df)}, expected {len(test_claims_df)}"
    )


def test_submission_column_names_and_order(submission_df, sample_submission_df):
    expected_cols = list(sample_submission_df.columns)
    assert list(submission_df.columns) == expected_cols, (
        f"Column mismatch: got {list(submission_df.columns)}, expected {expected_cols}"
    )


def test_submission_claim_id_order(submission_df, test_claims_df):
    expected_ids = list(test_claims_df["claim_id"])
    actual_ids = list(submission_df["claim_id"])
    assert actual_ids == expected_ids, "claim_id ordering does not match claims_test.csv"


def test_submission_decision_vocabulary(submission_df):
    valid_decisions = {"approve", "review"}
    unique_decisions = set(submission_df["decision"].dropna().unique())
    assert unique_decisions.issubset(valid_decisions), (
        f"Invalid decision values detected: {unique_decisions - valid_decisions}"
    )


def test_submission_date_format_when_present(submission_df):
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for val in submission_df["receipt_date"].dropna():
        if str(val).strip():
            assert date_regex.match(str(val)), f"Invalid date format: {val} (expected YYYY-MM-DD)"


def test_submission_amount_format_when_present(submission_df):
    for val in submission_df["total_amount"].dropna():
        if str(val).strip():
            try:
                amt = float(val)
                assert amt >= 0.0
            except ValueError:
                pytest.fail(f"Invalid total_amount format: {val}")


def test_submission_reasons_present(submission_df):
    empty_reasons = submission_df["reason"].isna() | (submission_df["reason"].str.strip() == "")
    assert not empty_reasons.any(), "Empty decision reasons detected in predictions.csv"
