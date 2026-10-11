"""Receipt field extraction engine for Indian business expense documents.

Extracts the five mandatory fields: vendor_name, bill_date, bill_number, gstin, bill_amount
using layout analysis, regex anchors, merchant dictionaries, and line-item disambiguation.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from .normalization import (
    normalize_amount,
    normalize_bill_number,
    normalize_date,
    normalize_vendor_name,
    validate_gstin,
    GSTIN_REGEX,
)
from .ocr import OCRResult
from .observability import logger


class ReceiptFields(BaseModel):
    """Core five extracted bill fields matching Tarang submission schema."""
    vendor_name: Optional[str] = Field(default=None, description="Vendor / Merchant name printed on bill")
    bill_date: Optional[str] = Field(default=None, description="Bill date in ISO YYYY-MM-DD")
    bill_number: Optional[str] = Field(default=None, description="Invoice / Bill / Ticket number")
    gstin: Optional[str] = Field(default=None, description="15-character GSTIN if printed, else None")
    bill_amount: Optional[float] = Field(default=None, description="Total payable bill amount in INR")


class FieldMetadata(BaseModel):
    """Metadata tracking field status, confidence, raw text evidence, and warnings."""
    status: str = "extracted"  # 'extracted' | 'missing' | 'ambiguous'
    confidence: Optional[float] = None
    evidence: str = ""
    warnings: List[str] = Field(default_factory=list)


class ExtractedReceipt(BaseModel):
    """Full extraction bundle including parsed fields, metadata, and OCR provenance."""
    fields: ReceiptFields
    metadata: Dict[str, FieldMetadata] = Field(default_factory=dict)
    raw_text: str = ""
    provider_name: str = "unknown"
    ocr_confidence: float = 0.0


# Regional Merchant Dictionary for Nagpur Division field vendors
KNOWN_REGIONAL_MERCHANTS = [
    "Sitabuldi Multilevel Parking",
    "Laxmi Auto Fuels",
    "Shree Sai Petroleum",
    "Om Sai Fuel Point",
    "New Highway Service Station",
    "Jai Ambe Fuels",
    "Highway King Dhaba",
    "Punjabi Tadka Dhaba",
    "Hotel Rajdhani Dhaba",
    "Hotel Saibaba Bhojnalaya",
    "Hotel Pradeep Pure Veg",
    "Ashirwad Veg Restaurant",
    "Spice Route Kitchen",
    "Annapurna Dining Hall",
    "Sai Ram Tea & Snacks",
    "Hotel Shubham",
    "Hotel Krishna Comforts",
    "Hotel Centre Point",
    "Hotel Radisson Blu",
    "Shree Ganesh Tours & Travels",
    "Royal Travels",
    "Maa Durga Cab Service",
    "Nagpur City Cabs",
    "Vidarbha Express Courier",
    "Prompt Parcel Services",
    "Maruti Courier",
    "DTDC Courier",
    "Nagpur Municipal Corporation Parking",
]


class ReceiptExtractor:
    """Extracts 5 required fields from raw OCR text with evidence snippets."""

    def __init__(self, known_merchants: List[str] = KNOWN_REGIONAL_MERCHANTS) -> None:
        self.known_merchants = known_merchants

    def extract(self, ocr_result: OCRResult) -> ExtractedReceipt:
        raw_text = ocr_result.text or ""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        metadata: Dict[str, FieldMetadata] = {}

        # 1. Extract GSTIN
        gstin_val, gstin_meta = self._extract_gstin(lines, raw_text)
        metadata["gstin"] = gstin_meta

        # 2. Extract Bill Date
        date_val, date_meta = self._extract_date(lines, raw_text)
        metadata["bill_date"] = date_meta

        # 3. Extract Bill Number
        bill_no_val, bill_no_meta = self._extract_bill_number(lines, raw_text)
        metadata["bill_number"] = bill_no_meta

        # 4. Extract Bill Amount
        amount_val, amount_meta = self._extract_amount(lines, raw_text)
        metadata["bill_amount"] = amount_meta

        # 5. Extract Vendor Name
        vendor_val, vendor_meta = self._extract_vendor(lines, raw_text)
        metadata["vendor_name"] = vendor_meta

        fields = ReceiptFields(
            vendor_name=vendor_val,
            bill_date=date_val,
            bill_number=bill_no_val,
            gstin=gstin_val,
            bill_amount=amount_val,
        )

        return ExtractedReceipt(
            fields=fields,
            metadata=metadata,
            raw_text=raw_text,
            provider_name=ocr_result.provider_name,
            ocr_confidence=ocr_result.confidence,
        )

    def _extract_gstin(self, lines: List[str], text: str) -> Tuple[Optional[str], FieldMetadata]:
        """Extract valid 15-character Indian GSTIN."""
        # Try explicit keyword anchors first: 'GSTIN', 'GST NO', 'GST:'
        for line in lines:
            m = re.search(r"(?i)GST(?:IN|[\s\.\:\#\-_]*NO)?[\s\.\:\#\-_]*([0-3][0-9][A-Z0-9]{13})", line)
            if m:
                raw_cand = m.group(1).upper()
                is_valid, clean = validate_gstin(raw_cand)
                if is_valid:
                    return clean, FieldMetadata(status="extracted", confidence=0.98, evidence=line)
                elif len(raw_cand) == 15:
                    return raw_cand, FieldMetadata(status="extracted", confidence=0.75, evidence=line, warnings=["GSTIN format checksum warning"])

        # Scan text for general GSTIN pattern
        general_match = re.search(r"\b([0-3][0-9][A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b", text.upper())
        if general_match:
            cand = general_match.group(1)
            return cand, FieldMetadata(status="extracted", confidence=0.92, evidence=cand)

        return None, FieldMetadata(status="missing", confidence=None, evidence="")

    def _extract_date(self, lines: List[str], text: str) -> Tuple[Optional[str], FieldMetadata]:
        """Extract bill invoice date, avoiding due/print dates."""
        # 1. First check anchor lines: 'Date:', 'Bill Date:', 'Invoice Date:', 'Dt:', 'Date_'
        anchor_patterns = [
            r"(?i)\b(?:bill\s*date|invoice\s*date|inv\s*date|date|dt)[\s\:\_\-\.]*(\d{1,4}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            r"(?i)\b(?:dated)[\s\:\_\-\.]*(\d{1,4}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        ]
        for line in lines:
            for pat in anchor_patterns:
                m = re.search(pat, line)
                if m:
                    cand = m.group(1).strip()
                    iso, err = normalize_date(cand)
                    if iso:
                        return iso, FieldMetadata(status="extracted", confidence=0.95, evidence=line)

        # 2. Scan lines from top for any date
        for line in lines[:10]:
            d_cand = re.search(r"\b(\d{1,4}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b", line)
            if d_cand:
                iso, err = normalize_date(d_cand.group(1))
                if iso:
                    return iso, FieldMetadata(status="extracted", confidence=0.85, evidence=line)

        # 3. Global search
        g_cand = re.search(r"\b(\d{1,4}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b", text)
        if g_cand:
            iso, err = normalize_date(g_cand.group(1))
            if iso:
                return iso, FieldMetadata(status="extracted", confidence=0.70, evidence=g_cand.group(0))

        return None, FieldMetadata(status="missing", confidence=None, evidence="")

    def _extract_bill_number(self, lines: List[str], text: str) -> Tuple[Optional[str], FieldMetadata]:
        """Extract invoice or bill number using anchor keywords."""
        patterns = [
            r"(?i)\b(?:invoice|inv|bill|receipt|rcpt|memo|ticket|awb|token)[\s\.]*(?:no\.?|#|num|number)?[\s\:\-\._]*([A-Z0-9\/\-_]{2,20})",
            r"(?i)\b(?:inv|bill|ticket|rcpt)\s*#\s*([A-Z0-9\/\-_]+)",
            r"(?i)\b(?:no|s\.?no|sr\.?no)[\s\:\-\._]+([0-9]{3,10})\b",
        ]
        for line in lines:
            for pat in patterns:
                m = re.search(pat, line)
                if m:
                    cand = m.group(1).strip()
                    # Filter out common noise words captured accidentally
                    if cand.lower() not in ("date", "cash", "original", "gst", "total", "rupees", "paid", "amount", "order"):
                        clean_no = normalize_bill_number(cand)
                        if clean_no and len(clean_no) >= 2:
                            return clean_no, FieldMetadata(status="extracted", confidence=0.92, evidence=line)

        return None, FieldMetadata(status="missing", confidence=None, evidence="")

    def _extract_amount(self, lines: List[str], text: str) -> Tuple[Optional[float], FieldMetadata]:
        """Extract final payable total amount, distinguishing from subtotals and tax components."""
        # 1. Look for explicit total anchors on the same line
        explicit_patterns = [
            r"(?i)\b(?:grand\s+total|net\s+payable|total\s+amount|total\s+amt|final\s+total|total\s+due|amount\s+payable)\b[^\d\n]*([0-9,]+(?:\.[0-9]{1,2})?)",
            r"(?i)\b(?:total)\b[^\d\n]*([0-9,]+(?:\.[0-9]{1,2})?)",
            r"(?i)\b(?:paid|cash|amount|amt)\b[^\d\n]*([0-9,]+(?:\.[0-9]{1,2})?)",
        ]

        # Scan from bottom to top for same-line anchors
        for line in reversed(lines):
            for pat in explicit_patterns:
                m = re.search(pat, line)
                if m:
                    amt = normalize_amount(m.group(1))
                    if amt is not None and amt > 0:
                        return amt, FieldMetadata(status="extracted", confidence=0.90, evidence=line)

        # 2. Multi-line lookahead: if line i has Total/Amount anchor, check line i+1 and i+2
        for i, line in enumerate(lines):
            if re.search(r"(?i)\b(?:grand\s+total|total\s+rs|total|net\s+payable|amount\s+due|amount)\b", line):
                for lookahead in (1, 2):
                    if i + lookahead < len(lines):
                        next_line = lines[i + lookahead]
                        amt = normalize_amount(next_line)
                        if amt is not None and amt > 0:
                            return amt, FieldMetadata(status="extracted", confidence=0.88, evidence=f"{line} -> {next_line}")

        # 3. Search for currency symbols / 'Rs' across lines
        currency_amounts = []
        for line in lines:
            m = re.findall(r"(?i)(?:rs\.?|inr|₹)\s*([0-9,]+(?:\.[0-9]{1,2})?)", line)
            for raw_m in m:
                a = normalize_amount(raw_m)
                if a is not None and a > 0:
                    currency_amounts.append((a, line))

        if currency_amounts:
            final_amt, line_ev = currency_amounts[-1]
            return final_amt, FieldMetadata(status="extracted", confidence=0.75, evidence=line_ev)

        # 4. Fallback: inspect lines from bottom up for trailing numbers (often grand total)
        for line in reversed(lines[:15]):
            m = re.search(r"[\|\:\-\s]+([0-9]{2,6}(?:\.[0-9]{1,2})?)\s*$", line)
            if m:
                a = normalize_amount(m.group(1))
                if a is not None and a > 0:
                    return a, FieldMetadata(status="extracted", confidence=0.65, evidence=line)

        return None, FieldMetadata(status="missing", confidence=None, evidence="")

    def _extract_vendor(self, lines: List[str], text: str) -> Tuple[Optional[str], FieldMetadata]:
        """Extract merchant name using regional dictionary matching or top-line layout heuristics."""
        # 1. Match against known regional merchants first
        text_lower = text.lower()
        for merchant in self.known_merchants:
            # Check if merchant name is substring in text
            if merchant.lower() in text_lower:
                return merchant, FieldMetadata(status="extracted", confidence=0.95, evidence=merchant)

        # 2. Fallback: inspect top 3 non-empty lines (retail receipts place merchant in header)
        for line in lines[:4]:
            # Filter out headers that are generic labels like 'Tax Invoice', 'Cash Receipt', 'Date'
            if re.search(r"(?i)^(?:tax\s+invoice|cash\s+memo|retail\s+invoice|bill\s+of\s+supply|receipt|original|customer\s+copy)$", line):
                continue
            if len(line) >= 3 and not re.search(r"^\d+$", line):
                norm_vendor = normalize_vendor_name(line)
                if norm_vendor:
                    return norm_vendor, FieldMetadata(status="extracted", confidence=0.70, evidence=line)

        return None, FieldMetadata(status="missing", confidence=None, evidence="")
