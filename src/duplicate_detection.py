"""Duplicate receipt and invoice collision detector.

Implements perceptual image hashing (dHash) and invoice fingerprinting
(vendor + bill_number + amount) to detect identical or re-submitted claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from PIL import Image

from .observability import logger


@dataclass
class DuplicateCheckResult:
    """Result of duplicate check."""
    is_duplicate: bool = False
    match_type: Optional[str] = None  # 'image_hash_exact' | 'invoice_number_collision' | 'none'
    matching_claim_id: Optional[str] = None
    confidence: float = 0.0
    details: str = ""


class DuplicateDetector:
    """Tracks processed claims to flag duplicate receipts and invoice re-submissions."""

    def __init__(self) -> None:
        # Maps dHash (hex string) -> list of claim_ids
        self.image_hashes: Dict[str, str] = {}
        # Maps (vendor_normalized, bill_number) -> claim_id
        self.invoice_keys: Dict[Tuple[str, str], str] = {}
        # Maps bill_number (if unique/non-trivial) -> claim_id
        self.bill_numbers: Dict[str, str] = {}

    @staticmethod
    def compute_dhash(image: Image.Image, hash_size: int = 8) -> str:
        """Compute difference hash (dHash) of PIL image for visual near-duplicate detection."""
        # Convert to grayscale and resize to (hash_size + 1, hash_size)
        resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        import numpy as np
        pixels = np.array(resized).flatten().tolist()

        # Compare adjacent pixels in each row
        diff = []
        for row in range(hash_size):
            for col in range(hash_size):
                left_idx = row * (hash_size + 1) + col
                right_idx = left_idx + 1
                diff.append(pixels[left_idx] > pixels[right_idx])

        # Convert boolean list to hex string
        decimal_val = 0
        hex_len = (hash_size * hash_size) // 4
        for bit in diff:
            decimal_val = (decimal_val << 1) | int(bit)

        return f"{decimal_val:0{hex_len}x}"

    def register_claim(
        self,
        claim_id: str,
        image: Optional[Image.Image] = None,
        vendor_name: Optional[str] = None,
        bill_number: Optional[str] = None,
    ) -> None:
        """Register a processed claim in the detector index."""
        if image is not None:
            try:
                img_hash = self.compute_dhash(image)
                self.image_hashes[img_hash] = claim_id
            except Exception as e:
                logger.debug(f"Failed to compute dHash for claim {claim_id}: {e}")

        if bill_number and len(bill_number) >= 3 and bill_number.lower() not in ("none", "null", "nil"):
            self.bill_numbers[bill_number.lower()] = claim_id
            if vendor_name:
                self.invoice_keys[(vendor_name.lower(), bill_number.lower())] = claim_id

    def check_duplicate(
        self,
        current_claim_id: str,
        image: Optional[Image.Image] = None,
        vendor_name: Optional[str] = None,
        bill_number: Optional[str] = None,
    ) -> DuplicateCheckResult:
        """Check whether the current claim collides with an already registered receipt."""
        # 1. Check invoice number collision
        if bill_number and len(bill_number) >= 3 and bill_number.lower() not in ("none", "null", "nil"):
            b_key = bill_number.lower()
            if vendor_name:
                v_key = (vendor_name.lower(), b_key)
                if v_key in self.invoice_keys and self.invoice_keys[v_key] != current_claim_id:
                    matched_id = self.invoice_keys[v_key]
                    return DuplicateCheckResult(
                        is_duplicate=True,
                        match_type="invoice_number_collision",
                        matching_claim_id=matched_id,
                        confidence=0.98,
                        details=f"Identical vendor '{vendor_name}' and bill number '{bill_number}' previously claimed in {matched_id}",
                    )

            if b_key in self.bill_numbers and self.bill_numbers[b_key] != current_claim_id:
                matched_id = self.bill_numbers[b_key]
                return DuplicateCheckResult(
                    is_duplicate=True,
                    match_type="invoice_number_collision",
                    matching_claim_id=matched_id,
                    confidence=0.90,
                    details=f"Bill number '{bill_number}' previously claimed in {matched_id}",
                )

        # 2. Check visual perceptual image hash collision
        if image is not None:
            try:
                curr_hash = self.compute_dhash(image)
                if curr_hash in self.image_hashes and self.image_hashes[curr_hash] != current_claim_id:
                    matched_id = self.image_hashes[curr_hash]
                    return DuplicateCheckResult(
                        is_duplicate=True,
                        match_type="image_hash_exact",
                        matching_claim_id=matched_id,
                        confidence=0.99,
                        details=f"Receipt image visually identical to previously processed claim {matched_id}",
                    )
            except Exception as e:
                logger.debug(f"Failed to check dHash for claim {current_claim_id}: {e}")

        return DuplicateCheckResult(is_duplicate=False, match_type="none", confidence=0.0, details="No duplicate detected")
