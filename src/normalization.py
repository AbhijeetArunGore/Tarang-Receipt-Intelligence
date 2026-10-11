"""Field normalization utilities for Indian expense receipts.

Handles Indian currency formats, multi-format date parsing to ISO YYYY-MM-DD,
GSTIN validation and formatting, and bill number/vendor string cleaning.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, Tuple


def normalize_amount(raw_val: Optional[str | float | int]) -> Optional[float]:
    """Normalize raw amount representations to clean float.
    Handles 'Rs. 1,234.50', 'Rs 500/-', '₹ 3,450.00', '3500.00', '1,200'.
    """
    if raw_val is None:
        return None

    if isinstance(raw_val, (int, float)):
        val = float(raw_val)
        return round(val, 2) if not (val != val) else None  # Check NaN

    text = str(raw_val).strip()
    if not text:
        return None

    # Remove currency prefixes, suffixes, and noise
    # e.g. Rs, Rs., Re, INR, /-, ₹
    text = re.sub(r"(?i)(?:rs\.?|inr|re\.?|₹|\/-)", "", text)
    # Remove commas used in Indian number formatting (e.g., 1,50,000 or 1,500.00)
    text = text.replace(",", "").strip()

    # Search for numeric pattern with optional decimals
    match = re.search(r"\b\d+(?:\.\d{1,2})?\b", text)
    if match:
        try:
            return round(float(match.group(0)), 2)
        except ValueError:
            return None

    return None


def normalize_date(raw_date: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Parse ambiguous or multi-format date strings into standard ISO YYYY-MM-DD.
    Returns (iso_date, error_or_warning).
    """
    if not raw_date:
        return None, "Empty date"

    text = str(raw_date).strip()
    # Normalize separators (convert dots, slashes to dashes if appropriate)
    text = re.sub(r"[\./]", "-", text)

    # Candidate date formats common in India
    formats = [
        "%Y-%m-%d",  # 2026-07-18
        "%d-%m-%Y",  # 18-07-2026
        "%d-%m-%y",  # 18-07-26
        "%d-%b-%Y",  # 18-Jul-2026
        "%d-%B-%Y",  # 18-July-2026
        "%Y-%m-%d",  # ISO
        "%m-%d-%Y",  # US format fallback
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            # Enforce reasonable century boundary if 2-digit year
            if dt.year < 2000:
                dt = dt.replace(year=dt.year + 100)
            return dt.strftime("%Y-%m-%d"), None
        except ValueError:
            continue

    # Try regex extraction for DD-MM-YYYY or YYYY-MM-DD embedded in text
    d_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if d_match:
        try:
            y, m, d = map(int, d_match.groups())
            dt = datetime(y, m, d)
            return dt.strftime("%Y-%m-%d"), None
        except ValueError:
            pass

    d_match2 = re.search(r"(\d{1,2})-(\d{1,2})-(\d{4})", text)
    if d_match2:
        try:
            d, m, y = map(int, d_match2.groups())
            dt = datetime(y, m, d)
            return dt.strftime("%Y-%m-%d"), None
        except ValueError:
            pass

    return None, f"Unrecognized date format: {raw_date}"


# Official Indian GSTIN 15-character Alphanumeric Regex
GSTIN_REGEX = re.compile(
    r"^[0-3][0-9][A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
)


def validate_gstin(raw_gstin: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate and normalize a 15-character Indian Goods and Services Tax Identification Number.
    Returns (is_valid, normalized_gstin).
    """
    if not raw_gstin:
        return False, None

    cleaned = re.sub(r"[\s\-_]", "", str(raw_gstin)).upper()

    if len(cleaned) != 15:
        return False, cleaned if cleaned else None

    if GSTIN_REGEX.match(cleaned):
        return True, cleaned

    return False, cleaned


def normalize_bill_number(raw_bill_no: Optional[str]) -> Optional[str]:
    """Normalize bill / invoice / receipt number, preserving meaningful letters, separators,
    and leading zeros, but removing noise labels like 'Bill No:', 'Inv #'.
    """
    if not raw_bill_no:
        return None

    text = str(raw_bill_no).strip()
    if not text or text.lower() in ("nan", "none", "null", "nil", "n/a"):
        return None

    # Strip prefixes like 'Invoice No:', 'Bill #', 'Receipt No.', 'Memo No:'
    cleaned = re.sub(
        r"(?i)^(?:invoice|inv|bill|receipt|rcpt|memo|tax\s+invoice|ticket|awb)\s*(?:no\.?|#|num|number)?\s*[:\-\.]?\s*",
        "",
        text,
    ).strip()

    # Remove trailing punctuation or whitespace
    cleaned = re.sub(r"[:;,]+$", "", cleaned).strip()

    return cleaned if cleaned else None


def normalize_vendor_name(raw_vendor: Optional[str]) -> Optional[str]:
    """Normalize merchant / vendor name, capitalizing properly and removing noise words."""
    if not raw_vendor:
        return None

    text = str(raw_vendor).strip()
    if not text or text.lower() in ("nan", "none", "null", "nil", "n/a"):
        return None

    # Remove noise like 'Welcome to', 'Tax Invoice', 'Cash Memo'
    cleaned = re.sub(r"(?i)^(?:welcome\s+to\s+|tax\s+invoice\s+|cash\s+memo\s+)", "", text).strip()
    # Normalize multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned.title() if cleaned.isupper() or cleaned.islower() else cleaned
