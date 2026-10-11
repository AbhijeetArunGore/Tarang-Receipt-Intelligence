"""Tarang Pharma Distribution field expense policy rules engine (Policy v3.2).

Encodes explicit policy thresholds, grade limits, mandatory GSTIN rules,
and approval routing with traceability back to policy sections.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .config import (
    AMOUNT_AUTO_APPROVE_MAX,
    FOOD_LIMIT_WITHOUT_APPROVAL,
    LODGING_LIMIT_M1_M2,
    LODGING_LIMIT_M3,
)
from .extraction import ExtractedReceipt


class PolicyAction(str, Enum):
    PASS = "PASS"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECT = "REJECT"


@dataclass
class PolicyEvaluationResult:
    """Traceable evaluation of an individual expense policy rule."""
    rule_id: str
    rule_name: str
    source_clause: str
    passed: bool
    action: PolicyAction
    evidence: str = ""
    reason: str = ""


@dataclass
class PolicyCheckSummary:
    """Consolidated summary of all policy rules evaluated for a claim."""
    all_passed: bool = True
    evaluations: List[PolicyEvaluationResult] = field(default_factory=list)

    @property
    def requires_review(self) -> bool:
        return any(e.action in (PolicyAction.MANUAL_REVIEW, PolicyAction.REJECT) for e in self.evaluations)

    def get_review_reasons(self) -> List[str]:
        return [e.reason for e in self.evaluations if e.action in (PolicyAction.MANUAL_REVIEW, PolicyAction.REJECT)]


class ExpensePolicyEngine:
    """Evaluates claims against Tarang Pharma Field Expense Policy v3.2."""

    def __init__(self) -> None:
        pass

    def evaluate(
        self,
        claim_data: Dict[str, Any],
        extracted: Optional[ExtractedReceipt],
        employee_info: Optional[Dict[str, Any]] = None,
    ) -> PolicyCheckSummary:
        results: List[PolicyEvaluationResult] = []

        category = str(claim_data.get("category", "")).strip().capitalize()
        claimed_amt = float(claim_data.get("amount_claimed_num", 0.0) or 0.0)
        grade = str(employee_info.get("grade", "M1")).strip().upper() if employee_info else "M1"

        # Rule POL_THRESHOLD_2000: Nilesh brief / Policy Section 7
        # Claims of Rs 2,000 and above must be checked by clerk
        if claimed_amt >= AMOUNT_AUTO_APPROVE_MAX:
            results.append(
                PolicyEvaluationResult(
                    rule_id="POL_HIGH_VALUE_THRESHOLD",
                    rule_name="High Value Claim Threshold",
                    source_clause="Section 7 (Proposed change): Claims of Rs 2,000 and above require clerk check",
                    passed=False,
                    action=PolicyAction.MANUAL_REVIEW,
                    evidence=f"Claimed amount ₹{claimed_amt:.2f} >= ₹{AMOUNT_AUTO_APPROVE_MAX:.2f}",
                    reason=f"Claim amount (₹{claimed_amt:.2f}) meets or exceeds ₹{AMOUNT_AUTO_APPROVE_MAX:.0f} high-value threshold; clerk review required",
                )
            )
        else:
            results.append(
                PolicyEvaluationResult(
                    rule_id="POL_HIGH_VALUE_THRESHOLD",
                    rule_name="High Value Claim Threshold",
                    source_clause="Section 7 (Proposed change)",
                    passed=True,
                    action=PolicyAction.PASS,
                    evidence=f"Claimed amount ₹{claimed_amt:.2f} < ₹{AMOUNT_AUTO_APPROVE_MAX:.2f}",
                )
            )

        # Rule POL_FOOD_LIMIT: Food up to Rs 2,500 without prior approval
        if category == "Food":
            if claimed_amt > FOOD_LIMIT_WITHOUT_APPROVAL:
                results.append(
                    PolicyEvaluationResult(
                        rule_id="POL_FOOD_CAP",
                        rule_name="Doctor / Stockist Meal Limit",
                        source_clause="Section 2: Meals with doctors/stockists up to Rs 2,500 without prior approval",
                        passed=False,
                        action=PolicyAction.MANUAL_REVIEW,
                        evidence=f"Claimed food expense ₹{claimed_amt:.2f} exceeds ₹{FOOD_LIMIT_WITHOUT_APPROVAL:.2f}",
                        reason=f"Food claim of ₹{claimed_amt:.2f} exceeds ₹{FOOD_LIMIT_WITHOUT_APPROVAL:.0f} limit without prior approval",
                    )
                )
            else:
                results.append(
                    PolicyEvaluationResult(
                        rule_id="POL_FOOD_CAP",
                        rule_name="Doctor / Stockist Meal Limit",
                        source_clause="Section 2",
                        passed=True,
                        action=PolicyAction.PASS,
                        evidence=f"₹{claimed_amt:.2f} <= ₹{FOOD_LIMIT_WITHOUT_APPROVAL:.2f}",
                    )
                )

        # Rule POL_LODGING: Lodging caps and mandatory GST invoice
        if category == "Lodging":
            cap = LODGING_LIMIT_M3 if grade == "M3" else LODGING_LIMIT_M1_M2
            if claimed_amt > cap:
                results.append(
                    PolicyEvaluationResult(
                        rule_id="POL_LODGING_CAP",
                        rule_name="Outstation Lodging Nightly Cap",
                        source_clause=f"Section 2: Grade {grade} up to Rs {cap:.0f} per night before GST",
                        passed=False,
                        action=PolicyAction.MANUAL_REVIEW,
                        evidence=f"Lodging amount ₹{claimed_amt:.2f} exceeds grade {grade} cap ₹{cap:.2f}",
                        reason=f"Lodging amount ₹{claimed_amt:.2f} exceeds Grade {grade} nightly limit of ₹{cap:.0f}",
                    )
                )
            else:
                results.append(
                    PolicyEvaluationResult(
                        rule_id="POL_LODGING_CAP",
                        rule_name="Outstation Lodging Nightly Cap",
                        source_clause="Section 2",
                        passed=True,
                        action=PolicyAction.PASS,
                        evidence=f"₹{claimed_amt:.2f} <= ₹{cap:.2f}",
                    )
                )

            # Hotel bill must be GST tax invoice (must have GSTIN)
            extracted_gstin = extracted.fields.gstin if extracted else None
            if not extracted_gstin:
                results.append(
                    PolicyEvaluationResult(
                        rule_id="POL_LODGING_GST_INVOICE",
                        rule_name="Hotel GST Tax Invoice Requirement",
                        source_clause="Section 2: Hotel bills must be GST tax invoices in employee's name",
                        passed=False,
                        action=PolicyAction.MANUAL_REVIEW,
                        evidence="No GSTIN found on hotel lodging receipt",
                        reason="Hotel lodging receipt lacks GST tax invoice identifier / GSTIN",
                    )
                )
            else:
                results.append(
                    PolicyEvaluationResult(
                        rule_id="POL_LODGING_GST_INVOICE",
                        rule_name="Hotel GST Tax Invoice Requirement",
                        source_clause="Section 2",
                        passed=True,
                        action=PolicyAction.PASS,
                        evidence=f"Valid GSTIN found: {extracted_gstin}",
                    )
                )

        # Check overall summary
        all_passed = not any(r.action in (PolicyAction.MANUAL_REVIEW, PolicyAction.REJECT) for r in results)
        return PolicyCheckSummary(all_passed=all_passed, evaluations=results)
