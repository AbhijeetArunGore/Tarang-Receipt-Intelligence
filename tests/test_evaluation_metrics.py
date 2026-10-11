"""Unit tests for evaluation metrics functions."""

import pytest
from src.evaluation import evaluate_field_accuracy, evaluate_decisions


def test_evaluate_field_accuracy():
    preds = ["100.0", "200.0", "300.0", None]
    refs = ["100.0", "205.0", "500.0", "400.0"]
    metrics = evaluate_field_accuracy(preds, refs, "bill_amount")
    assert metrics.total_evaluated == 4
    assert metrics.extracted_count == 3
    # 100==100 matches; 200 vs 205 is within 10 tolerance => matches!
    assert metrics.normalized_match_count == 2
    assert metrics.normalized_accuracy == 0.5


def test_evaluate_decisions():
    preds = ["approve", "review", "approve", "review"]
    refs = ["approve", "approve", "review", "review"]
    amounts = [100.0, 200.0, 300.0, 400.0]
    metrics = evaluate_decisions(preds, refs, amounts)
    assert metrics.total_claims == 4
    assert metrics.true_approvals == 1
    assert metrics.false_approvals == 1
    assert metrics.amount_weighted_false_approval_exposure_inr == 300.0
    assert metrics.accuracy == 0.5
