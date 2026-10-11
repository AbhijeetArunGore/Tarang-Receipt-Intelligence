"""Unit tests for Tarang Field Expense Policy v3.2 rules engine."""

import pytest

from src.policy import ExpensePolicyEngine, PolicyAction
from src.extraction import ExtractedReceipt, ReceiptFields


def test_sub_2000_threshold_pass():
    engine = ExpensePolicyEngine()
    claim = {"category": "Food", "amount_claimed_num": 450.0}
    extracted = ExtractedReceipt(fields=ReceiptFields(bill_amount=450.0))
    summary = engine.evaluate(claim, extracted)
    assert summary.all_passed is True
    assert not summary.requires_review


def test_above_2000_threshold_review():
    engine = ExpensePolicyEngine()
    claim = {"category": "Fuel", "amount_claimed_num": 2350.0}
    extracted = ExtractedReceipt(fields=ReceiptFields(bill_amount=2350.0))
    summary = engine.evaluate(claim, extracted)
    assert summary.all_passed is False
    assert summary.requires_review
    assert any(e.rule_id == "POL_HIGH_VALUE_THRESHOLD" for e in summary.evaluations)


def test_food_exceeding_2500_cap():
    engine = ExpensePolicyEngine()
    claim = {"category": "Food", "amount_claimed_num": 2800.0}
    extracted = ExtractedReceipt(fields=ReceiptFields(bill_amount=2800.0))
    summary = engine.evaluate(claim, extracted)
    assert summary.all_passed is False
    assert any(e.rule_id == "POL_FOOD_CAP" for e in summary.evaluations)


def test_lodging_without_gstin():
    engine = ExpensePolicyEngine()
    claim = {"category": "Lodging", "amount_claimed_num": 1800.0}
    # Hotel bill lacking GSTIN
    extracted = ExtractedReceipt(fields=ReceiptFields(bill_amount=1800.0, gstin=None))
    summary = engine.evaluate(claim, extracted)
    assert summary.all_passed is False
    assert any(e.rule_id == "POL_LODGING_GST_INVOICE" for e in summary.evaluations)
