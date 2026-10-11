"""Human-readable explanation generator for expense audit decisions.

Generates concise, evidence-backed audit rationale strictly aligned with
validation and policy findings without exposing sensitive employee PII.
"""

from __future__ import annotations

from typing import List, Optional
from src.policy import PolicyCheckSummary
from src.validation import ValidationResult


class ExplanationGenerator:
    """Produces concise, human-auditable reasons for approval and review decisions."""

    @staticmethod
    def generate_reason(
        decision: str,
        validation_result: Optional[ValidationResult] = None,
        policy_summary: Optional[PolicyCheckSummary] = None,
        image_status_msg: Optional[str] = None,
    ) -> str:
        """Compose clear explanation reason for submission and UI."""
        if decision == "approve":
            return "Receipt amount matches the submitted claim; mandatory fields and applicable policy checks passed."

        # Decision is 'review': prioritize specific blocking errors
        reasons: List[str] = []

        if image_status_msg and any(w in image_status_msg.lower() for w in ["missing", "not found", "upload failed", "unreadable", "degraded", "not exist"]):
            return "Review required: receipt image is unreadable or missing from upload."

        if validation_result and validation_result.has_blocking_errors:
            for f in validation_result.findings:
                if f.rule_id == "VAL_IMAGE_MISSING":
                    return "Review required: receipt image is unreadable or missing from upload."
                elif f.rule_id == "VAL_AMOUNT_MISMATCH":
                    return f"Review required: receipt amount differs from the submitted claim ({f.message})."
                elif f.rule_id == "VAL_AMOUNT_RECEIPT_MISSING":
                    return "Review required: bill amount could not be extracted reliably from receipt."
                elif f.rule_id == "VAL_DUPLICATE_COLLISION":
                    return f"Review required: possible duplicate invoice identifier ({f.details if hasattr(f, 'details') else f.message})."
                elif f.rule_id == "VAL_EMP_UNKNOWN":
                    return f"Review required: claimant employee ID not recognized in active roster."
                elif f.rule_id == "VAL_FUEL_VEHICLE_MISMATCH":
                    return f"Review required: vehicle registration on fuel receipt does not match employee record."
                elif f.rule_id == "VAL_DATE_MISMATCH":
                    return f"Review required: bill date differs from submitted expense date beyond tolerance."

            # General validation errors fallback
            val_errors = validation_result.get_error_reasons()
            if val_errors:
                return f"Review required: {val_errors[0]}"

        if policy_summary and policy_summary.requires_review:
            pol_reasons = policy_summary.get_review_reasons()
            if pol_reasons:
                return f"Review required: {pol_reasons[0]}"

        return "Review required: mandatory verification controls could not be verified automatically."
