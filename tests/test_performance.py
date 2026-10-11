"""Performance and latency boundary unit tests."""

import time
import pytest
from PIL import Image

from src.extraction import ReceiptExtractor
from src.ocr import MockOCRProvider
from src.validation import ClaimValidator
from src.policy import ExpensePolicyEngine
from src.decisions import DecisionEngine
from src.data import load_employees


def test_decision_pipeline_latency_under_mock():
    ocr = MockOCRProvider()
    extractor = ReceiptExtractor()
    try:
        emp_df = load_employees()
    except Exception:
        emp_df = None
    validator = ClaimValidator(employees_df=emp_df)
    policy = ExpensePolicyEngine()
    decision_engine = DecisionEngine(validator, policy)

    img = Image.new("RGB", (100, 100), color="white")

    start = time.perf_counter()
    res = ocr.extract_text(img)
    ext = extractor.extract(res)
    claim = {
        "claim_id": "CLM-P1",
        "emp_id": "TPD-0412",
        "amount_claimed": "1450.00",
        "amount_claimed_num": 1450.00,
        "category": "Food",
        "expense_date": "2026-07-15",
    }
    val = validator.validate(claim, ext)
    pol = policy.evaluate(claim, ext)
    dec = decision_engine.decide(claim, ext, val, pol)
    elapsed = (time.perf_counter() - start) * 1000.0

    # Whole pipeline should execute in under 100ms with mock
    assert elapsed < 100.0
    assert dec.decision in ("approve", "review")
