# Tarang Finance Operations — Clerk Runbook & Review Playbook

**Intended Audience:** Accounts Executive Priya Bhende & Finance Operations Team  
**System Role:** Human-in-the-Loop Review & Exception Handling  

---

## 1. Daily & Weekly Operational Workflow

1. **Batch Ingestion:** Every Monday morning, field expense uploads are synchronized.
2. **Automated Triage:** The Receipt Intelligence Platform processes the weekly batch.
   - **`approve` (Green):** Claims automatically scheduled for Friday reimbursement run.
   - **`review` (Amber):** Populated into the Finance Review Queue with pre-filled fields and specific audit flags.
3. **Clerk Review Time:** Because bill fields and validation findings are pre-extracted, reviewing an exception takes **~1.0 minute** (down from 3.5 minutes).

---

## 2. Review Flag Handling Protocol

| Audit Flag | What It Means | Action Required from Finance Clerk |
| :--- | :--- | :--- |
| `VAL_IMAGE_MISSING` | Receipt photo was not found on the server (upload failed). | Query claim back to rep: *"Please re-upload receipt photo in app."* |
| `VAL_AMOUNT_MISMATCH` | Extracted receipt amount differs from rep's claimed amount by $>$ ₹10. | Open image preview. If rep typed incorrect amount, adjust claim to bill total. If bill has multiple items, verify grand total. |
| `VAL_DUPLICATE_COLLISION` | Visual dHash or (vendor, bill no) collides with a previously submitted claim. | Inspect colliding claim ID listed in reason. If identical bill resubmitted, reject claim per Policy Section 8 (Misconduct). |
| `POL_LODGING_GST_INVOICE` | Hotel lodging receipt lacks GST tax invoice / GSTIN. | Query claim back to rep: *"Policy requires GST tax invoice in employee name."* |
| `POL_HIGH_VALUE_THRESHOLD` | Claim amount $\ge$ ₹2,000.00. | Routine managerial review: verify business necessity and manager approval note. |
| `VAL_FUEL_VEHICLE_MISMATCH` | Fuel bill shows different vehicle registration than employee roster. | Check if rep rented authorized vehicle or borrowed colleague's bike; require ASM sign-off. |
