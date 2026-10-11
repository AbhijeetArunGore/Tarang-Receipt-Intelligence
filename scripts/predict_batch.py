"""Batch prediction pipeline for Tarang Pharma expense claims.

Processes all claims in claims_test.csv, performs receipt OCR extraction,
validates against claim inputs and expense policy, and outputs predictions.csv
matching sample_submission.csv format exactly.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from src.config import (
    CLAIMS_TEST_PATH,
    CLAIMS_TRAIN_PATH,
    EMPLOYEES_PATH,
    PREDICTIONS_PATH,
    SAMPLE_SUBMISSION_PATH,
)
from src.data import (
    ImageResolutionStatus,
    ImageResolver,
    load_claims_test,
    load_claims_train,
    load_employees,
    load_sample_submission,
)
from src.decisions import DecisionEngine
from src.duplicate_detection import DuplicateDetector
from src.extraction import ReceiptExtractor
from src.image_processing import ImageProcessor
from src.normalization import normalize_amount
from src.ocr import get_ocr_provider
from src.policy import ExpensePolicyEngine
from src.validation import ClaimValidator


def run_batch_prediction() -> pd.DataFrame:
    print("=" * 60)
    print("Starting Tarang Pharma Batch Prediction Pipeline")
    print("=" * 60)

    # Load data
    test_df = load_claims_test()
    train_df = load_claims_train()
    emp_df = load_employees()
    sample_sub = load_sample_submission()

    print(f"Loaded {len(test_df)} test claims.")
    print(f"Loaded {len(train_df)} training claims for historical context.")

    # Initialize engines
    resolver = ImageResolver()
    ocr_provider = get_ocr_provider()
    extractor = ReceiptExtractor()
    duplicate_detector = DuplicateDetector()
    validator = ClaimValidator(employees_df=emp_df)
    policy_engine = ExpensePolicyEngine()
    decision_engine = DecisionEngine(validator=validator, policy_engine=policy_engine)

    print(f"Active OCR Provider: {ocr_provider.__class__.__name__} (available: {ocr_provider.is_available()})")

    # Pre-index training claims into duplicate detector
    print("Pre-indexing historical claims for duplicate prevention...")
    for _, row in train_df.iterrows():
        c_id = str(row["claim_id"])
        img_path, status, _ = resolver.resolve(row.get("image_file"))
        pil_img = None
        if img_path and img_path.exists():
            try:
                pil_img = ImageProcessor.load_image(img_path)
            except Exception:
                pass
        duplicate_detector.register_claim(
            claim_id=c_id,
            image=pil_img,
            vendor_name=str(row.get("clerk_vendor")) if pd.notna(row.get("clerk_vendor")) else None,
            bill_number=str(row.get("clerk_bill_no")) if pd.notna(row.get("clerk_bill_no")) else None,
        )

    results = []
    stats = {"processed": 0, "approved": 0, "reviewed": 0, "missing_images": 0}

    print("\nProcessing test claims...")
    for idx, row in test_df.iterrows():
        claim_id = str(row["claim_id"])
        image_ref = row.get("image_file")
        amount_claimed_raw = row.get("amount_claimed")
        amount_claimed_num = normalize_amount(amount_claimed_raw)

        claim_data = row.to_dict()
        claim_data["amount_claimed_num"] = amount_claimed_num

        # Resolve physical image file
        img_path, res_status, res_msg = resolver.resolve(image_ref)

        extracted = None
        val_res = None
        pol_res = None
        dup_res = None
        image_resolved = False

        if res_status == ImageResolutionStatus.RESOLVED and img_path and img_path.exists():
            try:
                pil_img = ImageProcessor.load_image(img_path)
                is_blank, blank_msg = ImageProcessor.is_blank_or_degraded(pil_img)

                if is_blank:
                    res_msg = f"Receipt image degraded: {blank_msg}"
                else:
                    image_resolved = True
                    # Run OCR
                    ocr_res = ocr_provider.extract_text(pil_img)

                    # Extract fields
                    extracted = extractor.extract(ocr_res)

                    # Check duplicate
                    dup_res = duplicate_detector.check_duplicate(
                        current_claim_id=claim_id,
                        image=pil_img,
                        vendor_name=extracted.fields.vendor_name,
                        bill_number=extracted.fields.bill_number,
                    )

                    # Register in detector for subsequent test claims
                    duplicate_detector.register_claim(
                        claim_id=claim_id,
                        image=pil_img,
                        vendor_name=extracted.fields.vendor_name,
                        bill_number=extracted.fields.bill_number,
                    )

                    # Validate against claim & employee roster
                    val_res = validator.validate(
                        claim_data=claim_data,
                        extracted=extracted,
                        duplicate_check=dup_res,
                        image_resolved=True,
                    )

                    # Check policy rules
                    emp_info = validator.employee_index.get(str(row.get("emp_id", "")).strip())
                    pol_res = policy_engine.evaluate(
                        claim_data=claim_data,
                        extracted=extracted,
                        employee_info=emp_info,
                    )

            except Exception as e:
                res_msg = f"Image processing exception: {str(e)}"
        else:
            stats["missing_images"] += 1

        # Decision
        audit_decision = decision_engine.decide(
            claim_data=claim_data,
            extracted=extracted,
            validation_result=val_res,
            policy_summary=pol_res,
            image_resolved=image_resolved,
            image_status_msg=res_msg,
        )

        stats["processed"] += 1
        if audit_decision.decision == "approve":
            stats["approved"] += 1
        else:
            stats["reviewed"] += 1

        # Serialize fields strictly conforming to sample_submission.csv
        v_out = extracted.fields.vendor_name if (extracted and extracted.fields.vendor_name) else ""
        d_out = extracted.fields.bill_date if (extracted and extracted.fields.bill_date) else ""
        n_out = extracted.fields.bill_number if (extracted and extracted.fields.bill_number) else ""
        g_out = extracted.fields.gstin if (extracted and extracted.fields.gstin) else ""
        a_out = extracted.fields.bill_amount if (extracted and extracted.fields.bill_amount is not None) else ""

        results.append({
            "claim_id": claim_id,
            "vendor": v_out,
            "receipt_date": d_out,
            "receipt_number": n_out,
            "gstin": g_out,
            "total_amount": a_out,
            "decision": audit_decision.decision,
            "reason": audit_decision.reason,
        })

        if stats["processed"] % 25 == 0 or stats["processed"] == len(test_df):
            print(f"Processed {stats['processed']}/{len(test_df)} claims... "
                  f"(Approved: {stats['approved']}, Review: {stats['reviewed']})")

    # Create DataFrame
    pred_df = pd.DataFrame(results)

    # Reorder columns strictly matching sample_submission.csv
    expected_cols = list(sample_sub.columns)
    pred_df = pred_df[expected_cols]

    # Save to root predictions.csv
    pred_df.to_csv(PREDICTIONS_PATH, index=False)
    print(f"\nSaved {len(pred_df)} predictions to {PREDICTIONS_PATH}")

    # Validation
    assert len(pred_df) == len(test_df), f"Row count mismatch: {len(pred_df)} != {len(test_df)}"
    assert list(pred_df.columns) == expected_cols, f"Columns mismatch: {list(pred_df.columns)} != {expected_cols}"
    assert set(pred_df["decision"].unique()).issubset({"approve", "review"}), "Invalid decision vocabulary"

    print("Predictions validation PASSED: Schema, row count, and vocabulary strictly match sample submission.")
    print(f"Final Summary: Total Claims={stats['processed']}, Approved={stats['approved']}, Review={stats['reviewed']} "
          f"(STP Auto-approval Rate: {stats['approved']/stats['processed']*100:.1f}%)")

    return pred_df


if __name__ == "__main__":
    run_batch_prediction()
