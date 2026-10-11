"""Deterministic decision engine for expense claim audit.

Evaluates multi-point validation and expense policy checks to emit strictly
'approve' or 'review' decisions accompanied by concise evidence-based explanations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from src.explanations import ExplanationGenerator
    from src.extraction import ExtractedReceipt
    from src.policy import ExpensePolicyEngine, PolicyCheckSummary
    from src.validation import ClaimValidator, ValidationResult
except (ImportError, ModuleNotFoundError):
    from explanations import ExplanationGenerator  # type: ignore
    from extraction import ExtractedReceipt  # type: ignore
    from policy import ExpensePolicyEngine, PolicyCheckSummary  # type: ignore
    from validation import ClaimValidator, ValidationResult  # type: ignore


ALLOWED_DECISIONS = {"approve", "review"}


@dataclass
class AuditDecision:
    """Final decision output for an individual claim."""
    claim_id: str
    decision: str  # 'approve' | 'review'
    reason: str
    validation_result: Optional[ValidationResult] = None
    policy_summary: Optional[PolicyCheckSummary] = None
    extracted_fields: Optional[Dict[str, Any]] = None


class DecisionEngine:
    """Enforces conservative, multi-factor deterministic controls for claim routing."""

    def __init__(
        self,
        validator: Optional[ClaimValidator] = None,
        policy_engine: Optional[ExpensePolicyEngine] = None,
    ) -> None:
        self.validator = validator or ClaimValidator()
        self.policy_engine = policy_engine or ExpensePolicyEngine()

    def decide(
        self,
        claim_data: Dict[str, Any],
        extracted: Optional[ExtractedReceipt],
        validation_result: Optional[ValidationResult],
        policy_summary: Optional[PolicyCheckSummary],
        image_resolved: bool = True,
        image_status_msg: Optional[str] = None,
    ) -> AuditDecision:
        claim_id = str(claim_data.get("claim_id", "UNKNOWN"))

        # Baseline checks: missing image or unreadable receipt
        if not image_resolved or extracted is None:
            reason = ExplanationGenerator.generate_reason(
                decision="review",
                validation_result=validation_result,
                policy_summary=policy_summary,
                image_status_msg=image_status_msg or "Image missing",
            )
            return AuditDecision(
                claim_id=claim_id,
                decision="review",
                reason=reason,
                validation_result=validation_result,
                policy_summary=policy_summary,
            )

        # Check blocking validation errors
        if validation_result and validation_result.has_blocking_errors:
            reason = ExplanationGenerator.generate_reason(
                decision="review",
                validation_result=validation_result,
                policy_summary=policy_summary,
            )
            return AuditDecision(
                claim_id=claim_id,
                decision="review",
                reason=reason,
                validation_result=validation_result,
                policy_summary=policy_summary,
            )

        # Check policy requirements
        if policy_summary and policy_summary.requires_review:
            reason = ExplanationGenerator.generate_reason(
                decision="review",
                validation_result=validation_result,
                policy_summary=policy_summary,
            )
            return AuditDecision(
                claim_id=claim_id,
                decision="review",
                reason=reason,
                validation_result=validation_result,
                policy_summary=policy_summary,
            )

        # All multi-factor controls passed -> APPROVE
        reason = ExplanationGenerator.generate_reason(
            decision="approve",
            validation_result=validation_result,
            policy_summary=policy_summary,
        )
        return AuditDecision(
            claim_id=claim_id,
            decision="approve",
            reason=reason,
            validation_result=validation_result,
            policy_summary=policy_summary,
        )
