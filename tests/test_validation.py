"""Unit tests for claim and receipt reconciliation validation."""

import pytest
import pandas as pd

from src.validation import ClaimValidator, ValidationSeverity
from src.extraction import ExtractedReceipt, ReceiptFields, FieldMetadata
from src.duplicate_detection import DuplicateCheckResult


@pytest.fixture
def sample_emp_df():
    return pd.DataFrame([
        {
            "emp_id": "TPD-0412",
            "name": "Rohan Wankhede",
            "designation": "Medical Representative",
            "headquarter": "Nagpur",
            "manager_id": "TPD-0301",
            "vehicle_no": "MH31 EK 4471",
            "grade": "M1",
        }
    ])


def test_validation_matching_claim(sample_emp_df):
    validator = ClaimValidator(employees_df=sample_emp_df)
    claim = {
        "claim_id": "CLM-100",
        "emp_id": "TPD-0412",
        "amount_claimed": "Rs. 350.00",
        "expense_date": "2026-07-20",
        "category": "Food",
    }
    extracted = ExtractedReceipt(
        fields=ReceiptFields(bill_amount=350.00, bill_date="2026-07-20", vendor_name="Hotel Rajdhani"),
        raw_text="HOTEL RAJDHANI Total 350",
    )
    res = validator.validate(claim, extracted)
    assert res.is_valid is True
    assert not res.has_blocking_errors


def test_validation_amount_mismatch(sample_emp_df):
    validator = ClaimValidator(employees_df=sample_emp_df)
    claim = {
        "claim_id": "CLM-101",
        "emp_id": "TPD-0412",
        "amount_claimed": "500",
        "expense_date": "2026-07-20",
        "category": "Food",
    }
    extracted = ExtractedReceipt(
        fields=ReceiptFields(bill_amount=350.00, bill_date="2026-07-20"),
    )
    res = validator.validate(claim, extracted)
    assert res.is_valid is False
    assert any(f.rule_id == "VAL_AMOUNT_MISMATCH" for f in res.findings)


def test_validation_missing_image(sample_emp_df):
    validator = ClaimValidator(sample_emp_df)
    claim = {"claim_id": "CLM-102", "emp_id": "TPD-0412", "amount_claimed": "300"}
    res = validator.validate(claim, extracted=None, image_resolved=False)
    assert res.is_valid is False
    assert any(f.rule_id == "VAL_IMAGE_MISSING" for f in res.findings)


def test_validation_duplicate_collision(sample_emp_df):
    validator = ClaimValidator(sample_emp_df)
    claim = {"claim_id": "CLM-103", "emp_id": "TPD-0412", "amount_claimed": "300"}
    extracted = ExtractedReceipt(fields=ReceiptFields(bill_amount=300.0))
    dup_res = DuplicateCheckResult(
        is_duplicate=True, match_type="invoice_number_collision", matching_claim_id="CLM-099", details="Duplicate bill"
    )
    res = validator.validate(claim, extracted, duplicate_check=dup_res)
    assert res.is_valid is False
    assert any(f.rule_id == "VAL_DUPLICATE_COLLISION" for f in res.findings)
