"""Claim and receipt reconciliation validation engine.

Performs multi-point deterministic verification comparing rep-submitted claims
against extracted receipt metadata and employee master records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd

from .config import AMOUNT_TOLERANCE_ABSOLUTE, DATE_TOLERANCE_DAYS
from .duplicate_detection import DuplicateCheckResult
from .extraction import ExtractedReceipt
from .normalization import normalize_amount, normalize_date


class ValidationSeverity(str, Enum):
    ERROR = "ERROR"      # Blocks auto-approval, forces review
    WARNING = "WARNING"  # Advisory flag, does not necessarily block alone
    INFO = "INFO"


@dataclass
class ValidationFinding:
    """Individual finding from claim-to-receipt verification."""
    rule_id: str
    field_name: Optional[str]
    severity: ValidationSeverity
    message: str
    expected: Optional[Any] = None
    observed: Optional[Any] = None


@dataclass
class ValidationResult:
    """Consolidated outcome of all validation checks."""
    is_valid: bool = True
    findings: List[ValidationFinding] = field(default_factory=list)

    @property
    def has_blocking_errors(self) -> bool:
        return any(f.severity == ValidationSeverity.ERROR for f in self.findings)

    def get_error_reasons(self) -> List[str]:
        return [f.message for f in self.findings if f.severity == ValidationSeverity.ERROR]


class ClaimValidator:
    """Validates rep claim against extracted receipt and employee records."""

    def __init__(self, employees_df: Optional[pd.DataFrame] = None) -> None:
        self.employees_df = employees_df
        self.employee_index: Dict[str, Dict[str, Any]] = {}
        if employees_df is not None and not employees_df.empty:
            for _, row in employees_df.iterrows():
                self.employee_index[str(row["emp_id"]).strip()] = row.to_dict()

    def validate(
        self,
        claim_data: Dict[str, Any],
        extracted: Optional[ExtractedReceipt],
        duplicate_check: Optional[DuplicateCheckResult] = None,
        image_resolved: bool = True,
    ) -> ValidationResult:
        findings: List[ValidationFinding] = []

        # 1. Image presence verification
        if not image_resolved or extracted is None:
            findings.append(
                ValidationFinding(
                    rule_id="VAL_IMAGE_MISSING",
                    field_name="image_file",
                    severity=ValidationSeverity.ERROR,
                    message="Receipt image is missing from server upload or unreadable",
                )
            )
            return ValidationResult(is_valid=False, findings=findings)

        # 2. Check duplicate submission
        if duplicate_check and duplicate_check.is_duplicate:
            findings.append(
                ValidationFinding(
                    rule_id="VAL_DUPLICATE_COLLISION",
                    field_name="receipt_number",
                    severity=ValidationSeverity.ERROR,
                    message=f"Possible duplicate invoice: {duplicate_check.details}",
                    expected=claim_data.get("claim_id"),
                    observed=duplicate_check.matching_claim_id,
                )
            )

        # 3. Employee Roster Verification
        emp_id = str(claim_data.get("emp_id", "")).strip()
        if not emp_id or emp_id not in self.employee_index:
            findings.append(
                ValidationFinding(
                    rule_id="VAL_EMP_UNKNOWN",
                    field_name="emp_id",
                    severity=ValidationSeverity.ERROR,
                    message=f"Claimant employee ID '{emp_id}' not found in active roster",
                    expected="Valid emp_id",
                    observed=emp_id,
                )
            )

        # 4. Amount Verification
        claimed_raw = claim_data.get("amount_claimed")
        claimed_num = normalize_amount(claimed_raw)
        extracted_num = extracted.fields.bill_amount

        if claimed_num is None:
            findings.append(
                ValidationFinding(
                    rule_id="VAL_AMOUNT_CLAIMED_INVALID",
                    field_name="amount_claimed",
                    severity=ValidationSeverity.ERROR,
                    message="Claimed amount is unparseable or missing",
                    observed=claimed_raw,
                )
            )
        elif extracted_num is None:
            findings.append(
                ValidationFinding(
                    rule_id="VAL_AMOUNT_RECEIPT_MISSING",
                    field_name="total_amount",
                    severity=ValidationSeverity.ERROR,
                    message="Total bill amount could not be extracted reliably from receipt",
                )
            )
        else:
            diff = abs(claimed_num - extracted_num)
            if diff > AMOUNT_TOLERANCE_ABSOLUTE:
                findings.append(
                    ValidationFinding(
                        rule_id="VAL_AMOUNT_MISMATCH",
                        field_name="total_amount",
                        severity=ValidationSeverity.ERROR,
                        message=f"Receipt amount (₹{extracted_num:.2f}) differs from claimed amount (₹{claimed_num:.2f}) beyond policy tolerance (±₹{AMOUNT_TOLERANCE_ABSOLUTE:.0f})",
                        expected=claimed_num,
                        observed=extracted_num,
                    )
                )

        # 5. Date Verification (Temporal alignment)
        claimed_date_raw = claim_data.get("expense_date")
        claimed_date_iso, _ = normalize_date(claimed_date_raw) if claimed_date_raw else (None, None)
        extracted_date_iso = extracted.fields.bill_date

        if claimed_date_iso and extracted_date_iso:
            try:
                dt_claim = datetime.strptime(claimed_date_iso, "%Y-%m-%d")
                dt_receipt = datetime.strptime(extracted_date_iso, "%Y-%m-%d")
                days_diff = abs((dt_claim - dt_receipt).days)
                if days_diff > DATE_TOLERANCE_DAYS:
                    findings.append(
                        ValidationFinding(
                            rule_id="VAL_DATE_MISMATCH",
                            field_name="receipt_date",
                            severity=ValidationSeverity.ERROR,
                            message=f"Receipt date ({extracted_date_iso}) differs from claimed date ({claimed_date_iso}) by {days_diff} days (tolerance: {DATE_TOLERANCE_DAYS} days)",
                            expected=claimed_date_iso,
                            observed=extracted_date_iso,
                        )
                    )
            except Exception:
                pass
        elif not extracted_date_iso:
            findings.append(
                ValidationFinding(
                    rule_id="VAL_DATE_EXTRACT_FAILED",
                    field_name="receipt_date",
                    severity=ValidationSeverity.WARNING,
                    message="Receipt date could not be extracted unambiguously",
                )
            )

        # 6. Fuel Category: Registered Vehicle Verification
        category = str(claim_data.get("category", "")).strip().lower()
        if category == "fuel" and emp_id in self.employee_index:
            emp_info = self.employee_index[emp_id]
            registered_veh = str(emp_info.get("vehicle_no", "")).replace(" ", "").upper()
            if registered_veh and extracted.raw_text:
                clean_ocr_text = extracted.raw_text.replace(" ", "").upper()
                # If a different vehicle number format like MH31... is visible and doesn't match
                import re
                veh_matches = re.findall(r"\b(MH\d{2}[A-Z]{1,2}\d{4})\b", clean_ocr_text)
                if veh_matches and registered_veh not in veh_matches:
                    findings.append(
                        ValidationFinding(
                            rule_id="VAL_FUEL_VEHICLE_MISMATCH",
                            field_name="vehicle_no",
                            severity=ValidationSeverity.ERROR,
                            message=f"Fuel bill shows vehicle ({veh_matches[0]}) differing from employee registered vehicle ({emp_info.get('vehicle_no')})",
                            expected=emp_info.get("vehicle_no"),
                            observed=veh_matches[0],
                        )
                    )

        is_valid = not any(f.severity == ValidationSeverity.ERROR for f in findings)
        return ValidationResult(is_valid=is_valid, findings=findings)
