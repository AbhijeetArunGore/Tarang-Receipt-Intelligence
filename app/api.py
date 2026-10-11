"""FastAPI REST API for Tarang Receipt Intelligence Platform.

Exposes:
- GET /health: Health check and OCR engine status.
- POST /predict: Accepts multipart receipt image upload and claim metadata,
                 returns extracted fields, policy audit trace, and approve/review decision.
"""

from __future__ import annotations

import io
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.config import API_HOST, API_PORT, OCR_PROVIDER
from src.data import load_employees
from src.decisions import DecisionEngine
from src.duplicate_detection import DuplicateDetector
from src.extraction import ExtractedReceipt, ReceiptExtractor, ReceiptFields
from src.image_processing import ImageProcessingError, ImageProcessor
from src.normalization import normalize_amount
from src.observability import StopWatch, logger
from src.ocr import get_ocr_provider
from src.policy import ExpensePolicyEngine
from src.validation import ClaimValidator


app = FastAPI(
    title="Tarang Receipt Intelligence API",
    description="Automated receipt OCR extraction and expense policy compliance engine for Tarang Pharma Distribution.",
    version="1.0.0",
)

# Initialize singletons
ocr_provider = get_ocr_provider()
extractor = ReceiptExtractor()
duplicate_detector = DuplicateDetector()
try:
    emp_df = load_employees()
except Exception:
    emp_df = None
validator = ClaimValidator(employees_df=emp_df)
policy_engine = ExpensePolicyEngine()
decision_engine = DecisionEngine(validator=validator, policy_engine=policy_engine)


class HealthResponse(BaseModel):
    status: str
    ocr_provider: str
    ocr_available: bool
    version: str


class PredictResponse(BaseModel):
    claim_id: str
    decision: str  # 'approve' | 'review'
    reason: str
    extracted_fields: ReceiptFields
    validation_status: str
    validation_errors: List[str]
    policy_checks_passed: bool
    policy_review_reasons: List[str]
    ocr_provider: str
    processing_time_ms: float
    warnings: List[str]


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Returns service health status and OCR engine availability."""
    return HealthResponse(
        status="healthy",
        ocr_provider=ocr_provider.__class__.__name__,
        ocr_available=ocr_provider.is_available(),
        version="1.0.0",
    )


@app.post("/predict", response_model=PredictResponse)
async def predict_claim(
    file: UploadFile = File(..., description="Photographed receipt image file (JPEG, PNG, WebP)"),
    claim_id: str = Form(..., description="Unique claim identifier, e.g. CLM-31086"),
    emp_id: str = Form(..., description="Claimant employee ID, e.g. TPD-0412"),
    category: str = Form(..., description="Expense category: Fuel, Food, Lodging, Local travel, Courier, Parking"),
    amount_claimed: str = Form(..., description="Amount claimed by representative, e.g. 450.00"),
    expense_date: Optional[str] = Form(None, description="Date of expense, e.g. 2026-07-20"),
    rep_comment: Optional[str] = Form(None, description="Optional representative comment"),
) -> PredictResponse:
    """Process an expense claim: reads receipt image, validates policy, and returns approve/review decision."""
    with StopWatch() as timer:
        warnings: List[str] = []

        # Validate file size and type
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        valid, msg = ImageProcessor.validate_file(content)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)

        # Decode image safely
        try:
            pil_img = ImageProcessor.load_image(content)
        except ImageProcessingError as e:
            return PredictResponse(
                claim_id=claim_id,
                decision="review",
                reason=f"Review required: receipt image is unreadable ({str(e)}).",
                extracted_fields=ReceiptFields(),
                validation_status="FAILED",
                validation_errors=[str(e)],
                policy_checks_passed=False,
                policy_review_reasons=["Unreadable image binary"],
                ocr_provider=ocr_provider.__class__.__name__,
                processing_time_ms=timer.elapsed_ms,
                warnings=["Corrupt or unreadable image upload"],
            )

        # Check OCR availability
        if not ocr_provider.is_available():
            return PredictResponse(
                claim_id=claim_id,
                decision="review",
                reason="Review required: OCR provider is not configured or unavailable on the server.",
                extracted_fields=ReceiptFields(),
                validation_status="UNVERIFIED",
                validation_errors=["OCR engine unavailable"],
                policy_checks_passed=False,
                policy_review_reasons=["OCR unavailable"],
                ocr_provider="none",
                processing_time_ms=timer.elapsed_ms,
                warnings=["Server OCR engine is not configured"],
            )

        # Perform OCR extraction
        ocr_res = ocr_provider.extract_text(pil_img)
        extracted = extractor.extract(ocr_res)

        # Check duplicate
        dup_res = duplicate_detector.check_duplicate(
            current_claim_id=claim_id,
            image=pil_img,
            vendor_name=extracted.fields.vendor_name,
            bill_number=extracted.fields.bill_number,
        )

        # Build claim record dictionary
        amt_num = normalize_amount(amount_claimed)
        claim_dict = {
            "claim_id": claim_id,
            "emp_id": emp_id,
            "category": category,
            "amount_claimed": amount_claimed,
            "amount_claimed_num": amt_num,
            "expense_date": expense_date,
            "rep_comment": rep_comment,
        }

        # Validation
        val_res = validator.validate(
            claim_data=claim_dict,
            extracted=extracted,
            duplicate_check=dup_res,
            image_resolved=True,
        )

        # Policy checks
        emp_info = validator.employee_index.get(emp_id.strip())
        pol_res = policy_engine.evaluate(
            claim_data=claim_dict,
            extracted=extracted,
            employee_info=emp_info,
        )

        # Decision
        audit_dec = decision_engine.decide(
            claim_data=claim_dict,
            extracted=extracted,
            validation_result=val_res,
            policy_summary=pol_res,
            image_resolved=True,
        )

        return PredictResponse(
            claim_id=claim_id,
            decision=audit_dec.decision,
            reason=audit_dec.reason,
            extracted_fields=extracted.fields,
            validation_status="PASSED" if val_res.is_valid else "FAILED",
            validation_errors=val_res.get_error_reasons(),
            policy_checks_passed=pol_res.all_passed,
            policy_review_reasons=pol_res.get_review_reasons(),
            ocr_provider=ocr_provider.__class__.__name__,
            processing_time_ms=round(timer.current_elapsed_ms, 2),
            warnings=warnings,
        )
