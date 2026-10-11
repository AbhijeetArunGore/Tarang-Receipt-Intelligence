"""Unit tests for receipt field extraction and metadata tracking."""

import pytest

from src.extraction import (
    ExtractedReceipt,
    ReceiptExtractor,
    ReceiptFields,
)
from src.ocr import OCRResult


def test_extract_all_fields_successful():
    text = """
    HOTEL RAJDHANI DHABA
    National Highway 6, Nagpur
    GSTIN: 27AABCR1234F1Z9
    Date: 22-07-2026
    Bill No: RD-8891
    ---------------------------
    1x Paneer Butter Masala  Rs. 250.00
    4x Roti                 Rs.  80.00
    1x Mineral Water        Rs.  20.00
    ---------------------------
    Subtotal:               Rs. 350.00
    CGST 2.5%:              Rs.   8.75
    SGST 2.5%:              Rs.   8.75
    Grand Total:            Rs. 367.50
    """
    ocr_res = OCRResult(text=text, provider_name="mock", confidence=0.95)
    extractor = ReceiptExtractor()
    extracted = extractor.extract(ocr_res)

    assert isinstance(extracted, ExtractedReceipt)
    assert extracted.fields.vendor_name == "Hotel Rajdhani Dhaba"
    assert extracted.fields.bill_date == "2026-07-22"
    assert extracted.fields.bill_number == "RD-8891"
    assert extracted.fields.gstin == "27AABCR1234F1Z9"
    assert extracted.fields.bill_amount == 367.50

    # Metadata
    assert extracted.metadata["gstin"].status == "extracted"
    assert extracted.metadata["bill_amount"].status == "extracted"


def test_extract_parking_receipt_without_gstin():
    text = """
    SITABULDI MULTILEVEL PARKING
    NMC NAGPUR
    Ticket No: TKT-0941
    Date: 2026-07-20
    Vehicle Type: 2-Wheeler
    Total Amount: Rs 30.00
    Paid: Cash
    """
    ocr_res = OCRResult(text=text, provider_name="mock", confidence=0.90)
    extractor = ReceiptExtractor()
    extracted = extractor.extract(ocr_res)

    assert extracted.fields.vendor_name == "Sitabuldi Multilevel Parking"
    assert extracted.fields.bill_date == "2026-07-20"
    assert extracted.fields.bill_number == "TKT-0941"
    assert extracted.fields.gstin is None  # Parking has no GSTIN
    assert extracted.fields.bill_amount == 30.00
    assert extracted.metadata["gstin"].status == "missing"


def test_extract_empty_ocr():
    ocr_res = OCRResult(text="", provider_name="none", status="unavailable")
    extractor = ReceiptExtractor()
    extracted = extractor.extract(ocr_res)

    assert extracted.fields.vendor_name is None
    assert extracted.fields.bill_date is None
    assert extracted.fields.bill_number is None
    assert extracted.fields.gstin is None
    assert extracted.fields.bill_amount is None
