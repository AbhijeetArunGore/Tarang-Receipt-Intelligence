"""Unit tests for the decision engine and explanation generation."""

import pytest

from src.decisions import DecisionEngine, ALLOWED_DECISIONS
from src.extraction import ExtractedReceipt, ReceiptFields
from src.policy import PolicyCheckSummary, PolicyEvaluationResult, PolicyAction
from src.validation import ValidationResult, ValidationFinding, ValidationSeverity


def test_approve_when_all_controls_pass():
    engine = DecisionEngine()
    claim = {"claim_id": "CLM-500", "amount_claimed": "300"}
    extracted = ExtractedReceipt(fields=ReceiptFields(bill_amount=300.0, bill_date="2026-07-20"))
    val_res = ValidationResult(is_valid=True, findings=[])
    pol_res = PolicyCheckSummary(all_passed=True, evaluations=[])

    decision = engine.decide(claim, extracted, val_res, pol_res, image_resolved=True)
    assert decision.decision == "approve"
    assert decision.decision in ALLOWED_DECISIONS
    assert "matches the submitted claim" in decision.reason


def test_review_on_validation_error():
    engine = DecisionEngine()
    claim = {"claim_id": "CLM-501", "amount_claimed": "500"}
    extracted = ExtractedReceipt(fields=ReceiptFields(bill_amount=300.0))
    val_res = ValidationResult(
        is_valid=False,
        findings=[
            ValidationFinding(
                rule_id="VAL_AMOUNT_MISMATCH",
                field_name="total_amount",
                severity=ValidationSeverity.ERROR,
                message="Amount mismatch",
            )
        ],
    )
    pol_res = PolicyCheckSummary(all_passed=True, evaluations=[])

    decision = engine.decide(claim, extracted, val_res, pol_res, image_resolved=True)
    assert decision.decision == "review"
    assert decision.decision in ALLOWED_DECISIONS
    assert "Review required" in decision.reason


def test_review_on_policy_check():
    engine = DecisionEngine()
    claim = {"claim_id": "CLM-502", "amount_claimed": "2500"}
    extracted = ExtractedReceipt(fields=ReceiptFields(bill_amount=2500.0))
    val_res = ValidationResult(is_valid=True, findings=[])
    pol_res = PolicyCheckSummary(
        all_passed=False,
        evaluations=[
            PolicyEvaluationResult(
                rule_id="POL_HIGH_VALUE_THRESHOLD",
                rule_name="High Value",
                source_clause="Section 7",
                passed=False,
                action=PolicyAction.MANUAL_REVIEW,
                reason="High value claim exceeds 2000 threshold",
            )
        ],
    )

    decision = engine.decide(claim, extracted, val_res, pol_res, image_resolved=True)
    assert decision.decision == "review"
    assert "Review required" in decision.reason


def test_review_on_missing_image():
    engine = DecisionEngine()
    claim = {"claim_id": "CLM-503", "amount_claimed": "100"}
    decision = engine.decide(claim, extracted=None, validation_result=None, policy_summary=None, image_resolved=False)
    assert decision.decision == "review"
    assert "unreadable or missing" in decision.reason
