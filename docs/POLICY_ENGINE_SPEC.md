# Tarang Field Expense Policy Engine — Technical Specification

**Policy Version:** v3.2  
**Owning Department:** Tarang Finance  
**System Module:** `src/policy.py`  

---

## 1. Rules Architecture

The policy engine implements a deterministic rule evaluation matrix. Each rule is defined as an isolated evaluation clause with traceable references to the official policy document.

---

## 2. Rule Definitions & Thresholds

| Rule ID | Rule Name | Source Clause | Category | Condition / Threshold | Default Action if Violated |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POL_HIGH_VALUE_THRESHOLD` | High-Value Approval Gate | Policy Section 7 | All Categories | Amount Claimed $\ge$ ₹2,000.00 | Route to `MANUAL_REVIEW` by clerk |
| `POL_FOOD_CAP` | Meal Without Approval Cap | Policy Section 2 | Food | Amount Claimed $>$ ₹2,500.00 | Route to `MANUAL_REVIEW` |
| `POL_LODGING_CAP` | Nightly Outstation Room Cap | Policy Section 2 | Lodging | Grade M1/M2: $>$ ₹3,000.00; Grade M3: $>$ ₹4,500.00 | Route to `MANUAL_REVIEW` |
| `POL_LODGING_GST_INVOICE` | Mandatory Hotel GST Tax Invoice | Policy Section 2 | Lodging | Receipt lacks valid 15-char GSTIN | Route to `MANUAL_REVIEW` |
| `POL_FUEL_VEHICLE` | Vehicle Registration Match | Policy Section 2 | Fuel | Bill vehicle no $\ne$ registered vehicle in `employees.csv` | Route to `MANUAL_REVIEW` |
| `POL_ROUNDING_TOLERANCE` | Policy Rounding Acceptance | Policy Section 3 | All Categories | $\mid\text{Claim} - \text{Receipt}\mid \le$ ₹10.00 | Accepted as compliant (`PASS`) |
| `POL_MISCONDUCT_DUPLICATE` | Duplicate Resubmission | Policy Section 8 | All Categories | Identical invoice or visual perceptual hash collision | Flag `MANUAL_REVIEW` (disciplinary flag) |

---

## 3. Decision Logic Flow

```text
Claim Input & Extracted Receipt
          │
          ▼
   Image Legible? ─── No ───► Route to REVIEW
          │ Yes
          ▼
   Duplicate Hash? ── Yes ──► Route to REVIEW
          │ No
          ▼
   Amount Mismatch > ₹10? ── Yes ──► Route to REVIEW
          │ No
          ▼
   Date Discrepancy > 3 Days? ── Yes ──► Route to REVIEW
          │ No
          ▼
   Policy Caps / GSTIN Check ── Fail ──► Route to REVIEW
          │ Pass
          ▼
   Eligible for Straight-Through Auto-Approval (APPROVE)
```
