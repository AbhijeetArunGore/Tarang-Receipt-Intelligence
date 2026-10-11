"""Evaluation metrics calculation for field-level OCR and audit decisions.

Calculates:
- Field-wise exact match accuracy, normalized accuracy, coverage, and error counts
- Decision confusion matrix, straight-through processing (STP) rate, false approval rate
- Amount-weighted financial exposure from incorrect approvals.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from .normalization import normalize_amount, normalize_date


@dataclass
class FieldMetric:
    """Metrics for an individual extracted bill field."""
    field_name: str
    total_evaluated: int
    extracted_count: int
    coverage: float  # proportion with nonempty value
    exact_match_count: int
    exact_match_accuracy: float
    normalized_match_count: int
    normalized_accuracy: float
    error_count: int
    error_examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DecisionMetrics:
    """Metrics for approve / review classification performance."""
    total_claims: int
    actual_approve_count: int
    actual_review_count: int
    predicted_approve_count: int
    predicted_review_count: int
    true_approvals: int
    false_approvals: int  # CRITICAL RISK: System auto-approved an invalid / non-compliant claim
    true_reviews: int
    false_reviews: int
    accuracy: float
    precision_approve: float
    recall_approve: float
    straight_through_processing_rate: float  # Percentage of claims automated
    human_review_rate: float
    amount_weighted_false_approval_exposure_inr: float = 0.0


def evaluate_field_accuracy(
    predictions: List[Optional[Any]],
    references: List[Optional[Any]],
    field_name: str,
    amounts: Optional[List[float]] = None,
) -> FieldMetric:
    """Calculate exact and normalized accuracy for a field against reference ground truth."""
    total = len(predictions)
    if total == 0:
        return FieldMetric(field_name, 0, 0, 0.0, 0, 0.0, 0, 0.0, 0)

    extracted_cnt = 0
    exact_cnt = 0
    norm_cnt = 0
    errors: List[Dict[str, Any]] = []

    for idx, (pred, ref) in enumerate(zip(predictions, references)):
        pred_str = "" if pd.isna(pred) or pred is None else str(pred).strip()
        ref_str = "" if pd.isna(ref) or ref is None else str(ref).strip()

        if pred_str:
            extracted_cnt += 1

        # Strict exact match
        if pred_str.lower() == ref_str.lower() and pred_str != "":
            exact_cnt += 1
        elif not pred_str and not ref_str:
            # Both missing
            exact_cnt += 1

        # Normalized match depending on field type
        matched = False
        if field_name in ("bill_amount", "total_amount"):
            p_val = normalize_amount(pred)
            r_val = normalize_amount(ref)
            if p_val is not None and r_val is not None and abs(p_val - r_val) <= 10.0:
                matched = True
            elif p_val is None and r_val is None:
                matched = True
        elif field_name in ("bill_date", "receipt_date"):
            p_dt, _ = normalize_date(pred)
            r_dt, _ = normalize_date(ref)
            if p_dt and r_dt and p_dt == r_dt:
                matched = True
            elif not p_dt and not r_dt:
                matched = True
        elif field_name == "gstin":
            p_g = str(pred).replace(" ", "").upper() if pred_str else ""
            r_g = str(ref).replace(" ", "").upper() if ref_str else ""
            if p_g == r_g:
                matched = True
        else:
            # String fields (vendor, bill_number)
            p_clean = pred_str.lower().replace(" ", "")
            r_clean = ref_str.lower().replace(" ", "")
            if p_clean == r_clean or (len(p_clean) > 4 and p_clean in r_clean) or (len(r_clean) > 4 and r_clean in p_clean):
                matched = True
            elif not p_clean and not r_clean:
                matched = True

        if matched:
            norm_cnt += 1
        else:
            if len(errors) < 5 and (pred_str or ref_str):
                errors.append({"index": idx, "predicted": pred_str, "reference": ref_str})

    coverage = round(extracted_cnt / total, 4)
    exact_acc = round(exact_cnt / total, 4)
    norm_acc = round(norm_cnt / total, 4)
    err_cnt = total - norm_cnt

    return FieldMetric(
        field_name=field_name,
        total_evaluated=total,
        extracted_count=extracted_cnt,
        coverage=coverage,
        exact_match_count=exact_cnt,
        exact_match_accuracy=exact_acc,
        normalized_match_count=norm_cnt,
        normalized_accuracy=norm_acc,
        error_count=err_cnt,
        error_examples=errors,
    )


def evaluate_decisions(
    predicted_decisions: List[str],
    reference_decisions: List[str],
    claim_amounts: Optional[List[float]] = None,
) -> DecisionMetrics:
    """Calculate decision accuracy, confusion matrix, STP rate, and false-approval risk."""
    total = len(predicted_decisions)
    assert total == len(reference_decisions)

    tp_approve = 0  # Pred approve, Ref approve
    fp_approve = 0  # Pred approve, Ref review (CRITICAL RISK)
    tn_review = 0   # Pred review, Ref review
    fn_review = 0   # Pred review, Ref approve

    amounts = claim_amounts or [0.0] * total
    fa_exposure = 0.0

    for pred, ref, amt in zip(predicted_decisions, reference_decisions, amounts):
        p_app = pred.lower() == "approve"
        r_app = ref.lower() == "approve"

        if p_app and r_app:
            tp_approve += 1
        elif p_app and not r_app:
            fp_approve += 1
            fa_exposure += float(amt or 0.0)
        elif not p_app and not r_app:
            tn_review += 1
        else:
            fn_review += 1

    act_approve = tp_approve + fn_review
    act_review = tn_review + fp_approve
    pred_approve = tp_approve + fp_approve
    pred_review = tn_review + fn_review

    accuracy = round((tp_approve + tn_review) / total, 4) if total else 0.0
    precision = round(tp_approve / pred_approve, 4) if pred_approve else 1.0
    recall = round(tp_approve / act_approve, 4) if act_approve else 1.0
    stp_rate = round(pred_approve / total, 4) if total else 0.0
    review_rate = round(pred_review / total, 4) if total else 0.0

    return DecisionMetrics(
        total_claims=total,
        actual_approve_count=act_approve,
        actual_review_count=act_review,
        predicted_approve_count=pred_approve,
        predicted_review_count=pred_review,
        true_approvals=tp_approve,
        false_approvals=fp_approve,
        true_reviews=tn_review,
        false_reviews=fn_review,
        accuracy=accuracy,
        precision_approve=precision,
        recall_approve=recall,
        straight_through_processing_rate=stp_rate,
        human_review_rate=review_rate,
        amount_weighted_false_approval_exposure_inr=round(fa_exposure, 2),
    )
