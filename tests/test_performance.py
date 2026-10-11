"""Performance and latency boundary unit tests."""

import time
import pytest
from PIL import Image

from src.extraction import ReceiptExtractor
from src.ocr import MockOCRProvider
from src.validation import ClaimValidator
from src.policy import ExpensePolicyEngine
from src.decisions import DecisionEngine


def test_decision_pipeline_latency_under_mock():
    ocr = MockOCRProvider()
    extractor = ReceiptExtractor()
    validator = ClaimValidator()
    policy = ExpensePolicyEngine()
    decision_engine = DecisionEngine(validator, policy)

    img = Image.new("RGB", (100, 100), color="white")

    start = time.perf_counter()
    res = ocr.extract_text(img)
    ext = extractor.extract(res)
    claim = {"claim_id": "CLM-P1", "amount_claimed": "1450.00", "category": "Food"}
    val = validator.validate(claim, ext)
    pol = policy.evaluate(claim, ext)
    dec = decision_engine.decide(claim, ext, val, pol)
    elapsed = (time.perf_counter() - start) * 1000.0

    # Whole pipeline should execute in under 50ms with mock
    assert elapsed < 50.0
    assert dec.decision == "approve"
