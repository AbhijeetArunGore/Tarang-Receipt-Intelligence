"""Unit tests for perceptual image hashing and invoice duplicate detection."""

import pytest
from PIL import Image

from src.duplicate_detection import DuplicateDetector, DuplicateCheckResult


def test_dhash_calculation():
    img1 = Image.new("RGB", (100, 100), color="white")
    hash1 = DuplicateDetector.compute_dhash(img1)
    assert isinstance(hash1, str)
    assert len(hash1) == 16  # 64 bits = 16 hex chars


def test_duplicate_image_detection():
    detector = DuplicateDetector()
    img = Image.new("RGB", (100, 100), color="blue")

    # Register first claim
    detector.register_claim(claim_id="CLM-1001", image=img)

    # Check identical image submitted in second claim
    result = detector.check_duplicate(current_claim_id="CLM-1002", image=img)
    assert result.is_duplicate is True
    assert result.match_type == "image_hash_exact"
    assert result.matching_claim_id == "CLM-1001"


def test_duplicate_bill_number_detection():
    detector = DuplicateDetector()
    detector.register_claim(
        claim_id="CLM-2001",
        vendor_name="Hotel Shubham",
        bill_number="INV-9988",
    )

    # Check collision
    result = detector.check_duplicate(
        current_claim_id="CLM-2002",
        vendor_name="Hotel Shubham",
        bill_number="INV-9988",
    )
    assert result.is_duplicate is True
    assert result.match_type == "invoice_number_collision"
    assert result.matching_claim_id == "CLM-2001"


def test_non_duplicate():
    detector = DuplicateDetector()
    detector.register_claim(
        claim_id="CLM-3001",
        vendor_name="Laxmi Auto Fuels",
        bill_number="RCP-101",
    )

    result = detector.check_duplicate(
        current_claim_id="CLM-3002",
        vendor_name="Shree Sai Petroleum",
        bill_number="RCP-102",
    )
    assert result.is_duplicate is False
